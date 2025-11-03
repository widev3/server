server="192.168.1.196"

# get session_id
sid="$(curl -X GET http://$server:5000/session/acquire | jq -r '.session_id')"
echo $sid

# set mount location
curl -X POST http://$server:5000/mount/location \
     -H "Content-Type: application/json" \
     -H "Authorization: $sid" \
     -d '{"lat": 45.3833, "lon": 10.668056, "height": 145}'

# set mount target by ra/dec
curl -X POST http://$server:5000/mount/target \
     -H "Content-Type: application/json" \
     -H "Authorization: $sid" \
     -d '{"ra":"15h21m24s","dec":"-33d6m12s"}'

# set mount target by alt/az
curl -X POST http://$server:5000/mount/target \
     -H "Content-Type: application/json" \
     -H "Authorization: $sid" \
     -d '{"az":"181d33m","alt":"11d19m"}'

# set mount absolute offset in ra/dec
curl -X POST http://$server:5000/mount/offset \
     -H "Content-Type: application/json" \
     -H "Authorization: $sid" \
     -d '{"absolute": {"ra":"18h33m","dec":"11d19m"}}'

# set mount absolute offset in alt/az
curl -X POST http://$server:5000/mount/offset \
     -H "Content-Type: application/json" \
     -H "Authorization: $sid" \
     -d '{"absolute": {"az":"181d33m","alt":"11d19m"}}'

# set mount relative offset in ra/dec
curl -X POST http://$server:5000/mount/offset \
     -H "Content-Type: application/json" \
     -H "Authorization: $sid" \
     -d '{"absolute": {"ra":"3m","dec":"1d19m"}}'

# set mount relative offset in alt/az
curl -X POST http://$server:5000/mount/offset \
     -H "Content-Type: application/json" \
     -H "Authorization: $sid" \
     -d '{"absolute": {"az":"1d33m","alt":"1d19m"}}'

# set mount timedelta offset
curl -X POST http://$server:5000/mount/offset \
     -H "Content-Type: application/json" \
     -H "Authorization: $sid" \
     -d '{"timedelta": 300}'

# run the mount in follow mode
curl -X GET http://$server:5000/mount/run?bh=follow \
     -H "Authorization: $sid"

read -p "Pause 10 seconds or press ENTER" -t 10

# stop the mount
curl -X GET http://$server:5000/mount/stop \
     -H "Authorization: $sid"

# run the mount in transit mode
curl -X GET http://$server:5000/mount/run?bh=transit \
     -H "Authorization: $sid"

read -p "Pause 10 seconds or press ENTER" -t 10

# stop the mount
curl -X GET http://$server:5000/mount/stop \
     -H "Authorization: $sid"

# run the mount in route mode
curl -X GET http://$server:5000/mount/run?bh=route \
     -H "Authorization: $sid"

# get status
curl -X GET http://$server:5000/mount/status \
     -H "Authorization: $sid"

# stop the mount
curl -X GET http://$server:5000/mount/stop \
     -H "Authorization: $sid"

# release session
curl -X GET http://$server:5000/session/release \
     -H "Authorization: $sid"