# Example session (raw JSON-RPC 2.0 messages)

This shows the exact messages exchanged over stdio between an MCP host/client
and `server/fittrack_server.py`. You can reproduce this by running
`python3 test_client.py` from the repo root.

## 1. Handshake

**Client -> Server**
```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"fittrack-test-client","version":"1.0"}}}
```

**Server -> Client**
```json
{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18","capabilities":{"tools":{}},"serverInfo":{"name":"fittrack-mcp-server","version":"1.0.0"}}}
```

**Client -> Server (notification, no response expected)**
```json
{"jsonrpc":"2.0","method":"notifications/initialized"}
```

## 2. Discover available tools

**Client -> Server**
```json
{"jsonrpc":"2.0","id":2,"method":"tools/list"}
```

**Server -> Client (abridged)**
```json
{"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":"crear_perfil","description":"...","inputSchema":{"...":"..."}}, "... 6 more tools ..."]}}
```

## 3. Create a user profile

**Client -> Server**
```json
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"crear_perfil","arguments":{"usuario":"carlos","peso_kg":78,"altura_cm":172,"edad":25,"sexo":"M","nivel_actividad":"moderado","objetivo":"bajar_grasa"}}}
```

**Server -> Client**
```json
{"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"{\"ok\": true, \"perfil\": {...}}"}],"isError":false}}
```

## 4. Calculate nutrition targets

**Client -> Server**
```json
{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"calcular_meta_nutricional","arguments":{"usuario":"carlos"}}}
```

**Server -> Client**
```json
{"jsonrpc":"2.0","id":4,"result":{"content":[{"type":"text","text":"{\"calorias_objetivo\": 2189, \"proteina_g\": 156, \"grasas_g\": 61, \"carbohidratos_g\": 254, \"bmr\": 1735, \"tdee\": 2689}"}],"isError":false}}
```

## 5. Generate a routine

**Client -> Server**
```json
{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"generar_rutina","arguments":{"usuario":"carlos","dias_por_semana":4,"nivel":"intermedio"}}}
```

## 6. Log a meal

**Client -> Server**
```json
{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"registrar_comida","arguments":{"usuario":"carlos","alimento":"Pechuga de pollo + arroz","cantidad_g":350,"calorias":520}}}
```

## 7. Log a completed workout

**Client -> Server**
```json
{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"registrar_entrenamiento","arguments":{"usuario":"carlos","rutina_dia":"Empuje (Push)","completado":true}}}
```

## 8. Sync phone/smartwatch activity

**Client -> Server**
```json
{"jsonrpc":"2.0","id":8,"method":"tools/call","params":{"name":"sincronizar_actividad","arguments":{"usuario":"carlos","pasos":8400,"calorias_activas":310,"dispositivo":"Apple Watch"}}}
```

## 9. Query progress

**Client -> Server**
```json
{"jsonrpc":"2.0","id":9,"method":"tools/call","params":{"name":"consultar_progreso","arguments":{"usuario":"carlos"}}}
```

**Server -> Client**
```json
{"jsonrpc":"2.0","id":9,"result":{"content":[{"type":"text","text":"{\"rango\": {...}, \"calorias_consumidas\": 520, \"calorias_objetivo\": 2189, \"pasos_totales\": 8400, \"calorias_activas_totales\": 310, \"entrenamientos_completados\": 1, ...}"}],"isError":false}}
```

## Error example: unknown tool

**Client -> Server**
```json
{"jsonrpc":"2.0","id":10,"method":"tools/call","params":{"name":"tool_que_no_existe","arguments":{}}}
```

**Server -> Client**
```json
{"jsonrpc":"2.0","id":10,"error":{"code":-32602,"message":"Herramienta desconocida: tool_que_no_existe"}}
```
