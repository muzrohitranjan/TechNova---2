import { useState, useEffect } from "react"
import { supabase } from "./supabaseClient"

function App() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [message, setMessage] = useState("")
  const [user, setUser] = useState(null)

  // Check session on load
  useEffect(() => {
    const getSession = async () => {
      const { data } = await supabase.auth.getSession()
      setUser(data.session?.user || null)
    }
    getSession()
  }, [])

  const handleSignup = async () => {
    const { error } = await supabase.auth.signUp({ email, password })
    if (error) return setMessage(error.message)
    setMessage("Signup successful")
  }

  const handleLogin = async () => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
    if (error) return setMessage(error.message)
    setUser(data.user)
    setMessage("Login successful")
  }

  const handleLogout = async () => {
    await supabase.auth.signOut()
    setUser(null)
    setMessage("Logged out")
  }

  const checkProfiles = async () => {
    const { data, error } = await supabase
      .from("profiles")
      .select("*")

    console.log("Logged in user:", user)
    console.log("Profiles result:", data)
    console.log("Error:", error)
  }

  return (
    <div style={{ padding: "40px" }}>
      <h2>Auth & RLS Test System</h2>

      <input
        placeholder="Email"
        onChange={(e) => setEmail(e.target.value)}
      />
      <br /><br />

      <input
        type="password"
        placeholder="Password"
        onChange={(e) => setPassword(e.target.value)}
      />
      <br /><br />

      <button onClick={handleSignup}>Sign Up</button>
      <button onClick={handleLogin} style={{ marginLeft: "10px" }}>
        Login
      </button>
      <button onClick={handleLogout} style={{ marginLeft: "10px" }}>
        Logout
      </button>

      <br /><br />

      <button onClick={checkProfiles}>Check Profiles (RLS Test)</button>

      <p>{message}</p>

      {user && (
        <p>
          Logged in as: <strong>{user.email}</strong>
        </p>
      )}
    </div>
  )
}

export default App