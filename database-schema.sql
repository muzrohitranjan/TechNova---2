-- Profiles Table
CREATE TABLE profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    full_name TEXT,
    role TEXT CHECK (role IN ('user', 'admin')) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Recipes Table
CREATE TABLE recipes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    created_by UUID REFERENCES profiles(id),
    created_at TIMESTAMP DEFAULT NOW()
);