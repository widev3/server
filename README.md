## /session route

The session endpoint is used to acquire or release the session since only one session is allowed at a time.

### GET /session/acquire
#### response
```json
{
     "session_id": session_id
}
```

#### example
```bash
sid="$(curl -X GET http://$server:5000/session/acquire | jq -r '.session_id')"
echo $sid
```

### GET /session/release
#### response
* `{"message": "OK"}`, 200
* `{"message": "cannot release an empty session"}`, 403

#### example
```bash
curl -X GET http://$server:5000/session/release \
     -H "Authorization: $sid"
```

---
---

## /mount route

The route endpoint is used to move and manage everything related to the mechanics of the mount.

### POST /mount/location/
#### body
```json
{
     "lat": lat,
     "lon": lon,
     "height": height
}
```

#### response
* `{"message": "OK"}`, 200
* `{"error": "Missing required field lat"}`, 400
* `{"error": "Missing required field lon"}`, 400
* `{"error": "Empty body"}`, 400
* `{"error": "Missing required field height"}`, 400
* `{"error": "Already moving"}`, 403

#### example
```bash
curl -X POST http://$server:5000/mount/location \
     -H "Content-Type: application/json" \
     -H "Authorization: $sid" \
     -d '{"lat": 17.546, "lon": 15.786, "height": 12}'
```

---

### POST /mount/target
#### body
```json
{
     "ra": ra,
     "dec": dec
     "az": az,
     "alt": alt
}
```

#### response
* `{"message": "OK", "target": {"ra": ra_value,"dec": dec_value}}`, 200
* `{"error": "Empty body"}`, 400
* `{"error": "Missing required field target.dec"}`, 400
* `{"error": "Missing required field target.ra"}`, 400
* `{"error": "Missing required field target.az"}`, 400
* `{"error": "Missing required field target.alt"}`, 400
* `{"error": "Target should be in ra/dec or alt/az"}`, 400
* `{"error": "Neither ra/dec nor alt/az"}`, 400
* `{"error": "Already moving"}`, 403

#### example
```bash
curl -X POST http://$server:5000/mount/target \
     -H "Content-Type: application/json" \
     -H "Authorization: $sid" \
     -d '{"az":"181d33m","alt":"11d19m"}'
```

---

### POST /mount/offset
#### body
```json
{
     "absolute":
     {
          same_body_of_the_target_api
     },
     "relative":
     {
          same_body_of_the_target_api
     },
     "timedelta": timedelta
}
```

#### response
* `{"message": "OK", "offset": {"ra": ra_value,"dec": dec_value}}`, 200
* `{"error": "Empty body"}`, 400
* `{"error": "'absolute', 'relative' or 'timedelta'"}`, 400
* `{"error": "Already moving"}`, 403

#### example
```bash
curl -X POST http://$server:5000/mount/offset \
     -H "Content-Type: application/json" \
     -H "Authorization: $sid" \
     -d '{"absolute": {"ra":"18h33m","dec":"11d19m"}}'
```

---

### GET /mount/run?bh=
#### body
`/mount/run?bh=behaviour`

#### response
* `{"message": "OK"}`, 200
* `{"error": "Mount location is not set"}`, 400
* `{"error": "Mount target is not set"}`, 400
* `{"error": "Missing required argument bh"}`, 400
* `{"error": "bh must be 'follow', 'transit' or 'route'"}`, 400
* `{"error": f"Mount offset must be set when bh is {bh}"}`, 400

#### example
```bash
curl -X POST http://$server:5000/mount/run?bh=follow \
     -H "Content-Type: application/json" \
     -H "Authorization: $sid" \
     -d '{"az":"181d33m","alt":"11d19m"}'
```

---

### GET /mount/stop
#### response
* `{"message": "OK"}`, 200
* `{"error": "Already stopped"}`, 403

#### example
```bash
curl -X GET http://$server:5000/mount/stop \
     -H "Authorization: $sid"
```

### GET /mount/status
#### response
```json
{
     "location":
     {

     },
     "target":
     {

     },
     "offset":
     {

     },
     "position":
     {

     },
     "bh": hebaviour,
     "is_running": running_state
}
```

#### example
```bash
curl -X GET http://$server:5000/mount/status \
     -H "Authorization: $sid"
```

---
---

## middleware responses

Every API call must pass through a middleware to check the sender's trustworthiness.

#### response
* `{"error": "Unauthorized"}`, 401