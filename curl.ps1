curl -X POST "http://localhost:8000/generate_email" \
 -H "Content-Type: application/json" \
 -d '{
   "recipient_name": "Mr. Sharma",
   "recipient_email": "______",
   "company_name":"______",
   "role":"SDE Intern"
 }'


curl http://localhost:8000/status/1
curl -X POST http://localhost:8000/send_now/1
