import { createClient } from '@supabase/supabase-js'

const supabaseUrl = "https://bpwsiwjzshalucfvdiqe.supabase.co"
const supabaseKey = "sb_publishable_wHO1qUXe7YYLNlG6Cl9aaQ_a-zBilIt"

export const supabase = createClient(supabaseUrl, supabaseKey)