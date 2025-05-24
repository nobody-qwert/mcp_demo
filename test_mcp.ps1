# Test the /ask endpoint of the MCP demo server using PowerShell

$body = @'
{
  "messages": [
    {"role":"system","content":"You are connected to tools: create_user and get_user."},
    {"role":"user","content":"Please create a new user with id 2 and name Alice."}
  ]
}
'@

curl -Uri http://localhost:8080/ask `
     -Method POST `
     -Headers @{ "Content-Type" = "application/json" } `
     -Body $body
