# Auditoría forense ENUT 2024 — fase 1

Estado: **requiere revisión humana antes de staging o limpieza**.

Se inspeccionaron todos los registros de los cinco CSV. No se construyó ningún dataset ni se recodificaron valores. Los SHA-256 antes/después coinciden. El JSON contiene nombres exactos de columnas, perfiles por campo, distribuciones y evidencia completa.

## Archivos

| Tabla | Filas | Columnas | ID principal único y no vacío |
|---|---:|---:|---|
| TMODULO | 74,053 | 694 | LLAVEMOD: True |
| TSDEM | 94,565 | 33 | LLAVESDE: True |
| THOGAR | 29,181 | 60 | LLAVEHOG: True |
| TVIVIENDA | 28,714 | 38 | LLAVEVIV: True |
| TVAR_CREA | 74,053 | 60 | LLAVEMOD: True |

Separador detectado por archivo: coma; comillas dobles. Véase `encoding` en JSON: cuando todos los bytes son ASCII, no es posible identificar la codificación original entre UTF-8 y codificaciones heredadas compatibles. Se preservan ceros iniciales y cadenas vacías.

## Integridad de joins

| Relación | Cardinalidad observada | Sin match izquierda | Sin match derecha | Filas de inner join |
|---|---|---:|---:|---:|
| tmodulo.LLAVEMOD -> tsdem.LLAVESDE | one-to-one | 0 | 20512 | 74053 |
| tmodulo.LLAVEHOG -> thogar.LLAVEHOG | many-to-one | 0 | 0 | 74053 |
| tsdem.LLAVEHOG -> thogar.LLAVEHOG | many-to-one | 0 | 0 | 94565 |
| thogar.LLAVEVIV -> tvivienda.LLAVEVIV | many-to-one | 0 | 0 | 29181 |
| tmodulo.LLAVEVIV -> tvivienda.LLAVEVIV | many-to-one | 0 | 0 | 74053 |
| tmodulo.LLAVEMOD -> tvar_crea.LLAVEMOD | one-to-one | 0 | 0 | 74053 |
| tmodulo.LLAVEHOG -> tsdem.LLAVEHOG | many-to-many | 0 | 0 | 293913 |

**Unir TMODULO y TSDEM únicamente por hogar puede multiplicar personas.** La relación de persona se evalúa con LLAVEMOD ↔ LLAVESDE. Cardinalidad y cobertura se verificaron sobre cadenas exactas, sin normalización.

Concordancia de campos entre personas con llave coincidente:

```json
{
  "tsdem": {
    "LLAVEHOG_disagreements": 0,
    "LLAVEVIV_disagreements": 0,
    "SEXO_disagreements": 0,
    "CVE_ENT_disagreements": 0,
    "EDAD_V_disagreements": 0,
    "EST_DIS_disagreements": 0,
    "UPM_DIS_disagreements": 0
  },
  "tvar_crea": {
    "LLAVEHOG_disagreements": 0,
    "LLAVEVIV_disagreements": 0,
    "SEXO_disagreements": 0,
    "CVE_ENT_disagreements": 0,
    "EDAD_V_disagreements": 0,
    "EST_DIS_disagreements": 0,
    "UPM_DIS_disagreements": 0
  }
}
```

## Tamaños muestrales y ponderadores

Los conteos siguientes no aplican filtro de empleo. Los códigos de sexo se muestran sin etiquetas no verificadas. Las sumas positivas de FAC_PER no son estimaciones validadas de trabajadores. TSDEM contiene FAC_HOG; no se lo sustituye por FAC_PER.

| Tabla / dominio | n | Sexo (código: n) | Suma FAC_PER positivo |
|---|---:|---|---:|
| TMODULO / all_states_all_ages | 74053 | {"2": 39910, "1": 34143} | 107829510.0 |
| TMODULO / all_states_18_65 | 56118 | {"2": 30592, "1": 25526} | 81778765.0 |
| TMODULO / 09_all_ages | 2107 | {"1": 963, "2": 1144} | 8350019.0 |
| TMODULO / 09_18_65 | 1625 | {"2": 884, "1": 741} | 6431956.0 |
| TMODULO / 15_all_ages | 2647 | {"1": 1197, "2": 1450} | 15112996.0 |
| TMODULO / 15_18_65 | 2034 | {"1": 914, "2": 1120} | 11594651.0 |
| TMODULO / 09_15_18_65 | 3659 | {"2": 2004, "1": 1655} | 18026607.0 |
| TSDEM / all_states_all_ages | 94565 | {"2": 49866, "1": 44699} | None |
| TSDEM / all_states_18_65 | 58204 | {"2": 31449, "1": 26755} | None |
| TSDEM / 09_all_ages | 2361 | {"1": 1100, "2": 1261} | None |
| TSDEM / 09_18_65 | 1627 | {"2": 886, "1": 741} | None |
| TSDEM / 15_all_ages | 3249 | {"1": 1521, "2": 1728} | None |
| TSDEM / 15_18_65 | 2066 | {"1": 934, "2": 1132} | None |
| TSDEM / 09_15_18_65 | 3693 | {"2": 2018, "1": 1675} | None |
| TVAR_CREA / all_states_all_ages | 74053 | {"2": 39910, "1": 34143} | 107829510.0 |
| TVAR_CREA / all_states_18_65 | 56118 | {"1": 25526, "2": 30592} | 81778765.0 |
| TVAR_CREA / 09_all_ages | 2107 | {"1": 963, "2": 1144} | 8350019.0 |
| TVAR_CREA / 09_18_65 | 1625 | {"2": 884, "1": 741} | 6431956.0 |
| TVAR_CREA / 15_all_ages | 2647 | {"1": 1197, "2": 1450} | 15112996.0 |
| TVAR_CREA / 15_18_65 | 2034 | {"1": 914, "2": 1120} | 11594651.0 |
| TVAR_CREA / 09_15_18_65 | 3659 | {"2": 2004, "1": 1655} | 18026607.0 |

## Empleo

El protocolo exige una definición aprobada de empleo, pero aún no la especifica. P5_1, P5_2 y P5_7 se reportan por código original. El JSON incluye todas las variables P5, sin adjudicarles etiquetas.

```json
{
  "all_tmodulo": {
    "P5_1": {
      "1": 41787,
      "2": 32266
    },
    "P5_2": {
      "": 41787,
      "8": 29434,
      "1": 694,
      "2": 506,
      "7": 707,
      "6": 100,
      "5": 172,
      "3": 256,
      "4": 397
    },
    "P5_7": {
      "1": 24807,
      "": 48277,
      "2": 329,
      "3": 640
    }
  },
  "09_15_age18_65": {
    "P5_1": {
      "1": 2495,
      "2": 1164
    },
    "P5_2": {
      "": 2495,
      "8": 1059,
      "1": 23,
      "7": 37,
      "2": 13,
      "3": 12,
      "5": 3,
      "6": 1,
      "4": 16
    },
    "P5_7": {
      "1": 1434,
      "": 2053,
      "3": 126,
      "2": 46
    }
  }
}
```

## Traslado y combinaciones hora–minuto

El contrato identifica P5_9_1/P5_9_2 como horas/minutos de lunes a viernes. Se reportan componentes originales; no se genera una variable commute. Los pares completos con enteros no negativos, minutos 0–59 y horas ≤120 sólo superan un control aritmético. Esto no confirma validez según cuestionario. Horas >120 se señalan para revisión; no se eliminan.

| Dominio | Estado del par | n |
|---|---|---:|
| all_tmodulo | arithmetic_range_only_not_semantically_validated | 43583 |
| all_tmodulo | both_empty | 30470 |
| 09_15_age18_65 | arithmetic_range_only_not_semantically_validated | 2517 |
| 09_15_age18_65 | both_empty | 1142 |

### P5_9_1

```json
{
  "": 30470,
  "00": 11450,
  "01": 5293,
  "02": 6487,
  "03": 3258,
  "04": 1433,
  "05": 6701,
  "06": 1215,
  "07": 1035,
  "08": 691,
  "09": 115,
  "10": 3751,
  "11": 48,
  "12": 358,
  "13": 44,
  "14": 22,
  "15": 847,
  "16": 79,
  "17": 25,
  "18": 39,
  "19": 3,
  "20": 436,
  "21": 3,
  "22": 7,
  "23": 3,
  "24": 16,
  "25": 71,
  "26": 3,
  "27": 1,
  "28": 2,
  "30": 65,
  "32": 1,
  "35": 11,
  "38": 3,
  "40": 26,
  "44": 1,
  "45": 4,
  "48": 1,
  "50": 29,
  "56": 2,
  "60": 1,
  "64": 1,
  "72": 1,
  "85": 1
}
```

### P5_9_2

```json
{
  "": 30470,
  "00": 22344,
  "01": 304,
  "02": 110,
  "03": 58,
  "04": 35,
  "05": 625,
  "06": 35,
  "08": 141,
  "09": 2,
  "10": 1199,
  "12": 24,
  "14": 5,
  "15": 786,
  "16": 16,
  "18": 12,
  "20": 3458,
  "21": 2,
  "22": 1,
  "24": 9,
  "25": 939,
  "28": 15,
  "30": 6815,
  "32": 1,
  "33": 4,
  "35": 48,
  "36": 3,
  "37": 1,
  "38": 37,
  "40": 3544,
  "42": 3,
  "44": 1,
  "45": 234,
  "46": 1,
  "48": 21,
  "50": 2718,
  "52": 2,
  "54": 1,
  "55": 23,
  "56": 4,
  "58": 2
}
```

### P6_1_1_1

```json
{
  "00": 8,
  "01": 5,
  "02": 2,
  "03": 2,
  "04": 8,
  "05": 10,
  "06": 12,
  "07": 12,
  "08": 15,
  "09": 1,
  "10": 53,
  "11": 3,
  "12": 20,
  "13": 4,
  "14": 9,
  "15": 241,
  "16": 35,
  "17": 7,
  "18": 38,
  "19": 3,
  "20": 1192,
  "21": 28,
  "22": 47,
  "23": 13,
  "24": 147,
  "25": 3532,
  "26": 29,
  "27": 134,
  "28": 105,
  "29": 20,
  "30": 10417,
  "31": 39,
  "32": 465,
  "33": 61,
  "34": 75,
  "35": 15171,
  "36": 503,
  "37": 400,
  "38": 242,
  "39": 47,
  "40": 28168,
  "41": 55,
  "42": 464,
  "43": 55,
  "44": 49,
  "45": 6463,
  "46": 76,
  "47": 115,
  "48": 300,
  "49": 45,
  "50": 3785,
  "51": 5,
  "52": 49,
  "53": 7,
  "54": 13,
  "55": 531,
  "56": 32,
  "57": 11,
  "58": 6,
  "59": 1,
  "60": 489,
  "61": 1,
  "62": 9,
  "63": 1,
  "64": 4,
  "65": 55,
  "66": 6,
  "67": 2,
  "68": 1,
  "70": 36,
  "72": 4,
  "74": 2,
  "75": 21,
  "76": 1,
  "80": 10,
  "86": 1,
  "90": 5,
  "99": 20
}
```

### P6_1_1_2

```json
{
  "00": 72308,
  "01": 21,
  "02": 2,
  "03": 6,
  "05": 23,
  "06": 2,
  "07": 2,
  "08": 498,
  "09": 2,
  "10": 7,
  "12": 2,
  "15": 12,
  "16": 8,
  "20": 17,
  "25": 10,
  "30": 1037,
  "32": 1,
  "35": 2,
  "38": 6,
  "40": 22,
  "45": 6,
  "50": 35,
  "55": 4,
  "99": 20
}
```

El JSON contiene la distribución conjunta completa de horas y minutos, cruces con P5_1/P5_2 y controles de pares candidatos del módulo. Los pares fuera del contrato siguen pendientes de validación semántica.

## Vacíos, códigos especiales y diseño muestral

| Tabla | Celdas vacías | Campos con negativos numéricos | Diseño disponible |
|---|---:|---:|---|
| TMODULO | 35237106 | 0 | EST_DIS, UPM_DIS, FAC_PER |
| TSDEM | 508760 | 0 | EST_DIS, UPM_DIS, FAC_HOG |
| THOGAR | 635050 | 0 | EST_DIS, UPM_DIS, FAC_HOG |
| TVIVIENDA | 85915 | 0 | EST_DIS, UPM_DIS, FAC_VIV |
| TVAR_CREA | 1 | 0 | EST_DIS, UPM_DIS, FAC_PER |

Campos con vacíos en TVAR_CREA: {"ESCOLARIDAD": 1}.

### Alertas aritméticas en pares candidatos

| Par | Alertas (registros) |
|---|---|
| P6_1_1_1 + P6_1_1_2 | {"minute_above_59": 20} |
| P6_1_1_3 + P6_1_1_4 | {"minute_above_59": 20} |

Estas alertas pueden reflejar códigos especiales; no equivalen automáticamente a respuestas erróneas. En sueño P6_1_1_2 hay 20 valores `99`, pendientes de interpretación.

### Cobertura de TSDEM frente al módulo

De las 20,512 personas de TSDEM sin registro en TMODULO, 34 corresponden a edades 18–65 en entidades 09/15. No se atribuye la ausencia sólo a menores de edad; el motivo requiere documentación. El JSON desglosa edades y entidades.

Los perfiles por campo distinguen cadena vacía, espacios, candidatos textuales de ausencia y tokens de nueves repetidos. **No se interpreta 99/999/99999 como faltante sin diccionario**; pueden tener significados distintos según la variable.

Validación numérica de factores:

```json
{
  "tmodulo": {
    "FAC_PER": {
      "empty": 0,
      "nonnumeric": 0,
      "nonpositive": 0
    }
  },
  "tsdem": {
    "FAC_HOG": {
      "empty": 0,
      "nonnumeric": 0,
      "nonpositive": 0
    }
  },
  "thogar": {
    "FAC_HOG": {
      "empty": 0,
      "nonnumeric": 0,
      "nonpositive": 0
    }
  },
  "tvivienda": {
    "FAC_VIV": {
      "empty": 0,
      "nonnumeric": 0,
      "nonpositive": 0
    }
  },
  "tvar_crea": {
    "FAC_PER": {
      "empty": 0,
      "nonnumeric": 0,
      "nonpositive": 0
    }
  }
}
```

## Decisiones pendientes

1. Aprobar la población ocupada y sus códigos/filtros exactos.
2. Incorporar el diccionario y cuestionario oficiales para validar códigos especiales, universos, saltos, unidades y rangos de horas/minutos.
3. Confirmar los mapeos de autocuidado, convivencia familiar, ocio y horas de trabajo.
4. Resolver discrepancias de edad u otros campos, si aparecen arriba, sin sobrescribir información original.
5. Aprobar explícitamente cualquier exclusión o interpretación de ausencias antes de staging_v1.

## Reproducibilidad y límites

`python scripts/audit_enut_2024.py` (biblioteca estándar). Las frecuencias se calculan sobre cadenas originales y abarcan cada archivo completo. Los tipos inferidos describen la forma léxica, no el significado de la variable. Hashes, versión de Python y huellas de los protocolos están en el JSON.

No se modificó el pipeline; no corresponde reconstruir analytic_v1 en esta fase. No se certifica la validez del futuro dataset.
