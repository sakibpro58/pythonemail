// server.js

const express = require("express");
const { verify } = require("./lib/verify"); // Adjust this path based on where the verify function is located
const app = express();
const port = process.env.PORT || 3000;

// Root endpoint
app.get("/", (req, res) => {
  res.send("Welcome to the Email Verification Service!");
});

// Verify email API endpoint
app.get("/verify", async (req, res) => {
  const email = req.query.email;

  if (!email) {
    return res.status(400).json({ error: "Email query parameter is required" });
  }

  try {
    const result = await verify(email); // Assuming verify is async
    res.json({ email, valid: result });
  } catch (error) {
    res.status(500).json({ error: "Error verifying email", details: error.message });
  }
});

// Start the server
app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
