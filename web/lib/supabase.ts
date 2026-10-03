import "server-only";
import { createClient } from "@supabase/supabase-js";

// Read-only client: publishable key + RLS (SELECT only).
// Never put the service_role key in web/ — writes happen in the Python host or protected Route Handlers.
export function supabase() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
  if (!url || !key) {
    throw new Error("Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY (see .env.example)");
  }
  return createClient(url, key, { auth: { persistSession: false } });
}
