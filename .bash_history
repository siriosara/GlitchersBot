pkill -9 initdb
pkill -9 postgres
cat initdb.log
initdb -D $PREFIX/var/lib/postgresql --debug --no-sync --shared-memory-type=posix
initdb -D $PREFIX/var/lib/postgresql
rm -rf $PREFIX/var/lib/postgresqlinitdb -D $PREFIX/var/lib/postgresql --debug --no-sync
pg_ctl -D $PREFIX/var/lib/postgresql start
curl "https://api.telegram.org/botYOUR_BOT_TOKEN/getWebhookInfo"
curl "https://api.telegram.org/bot7665636304:AAEsWwMX7QG4tVoC3IufpSjL-ZMjfspIphY/getWebhookInfo"
curl -X GET "https://api.telegram.org/bot<7665636304:AAEsWwMX7QG4tVoC3IufpSjL-ZMjfspIphY>/getWebhookInfo"
curl -X GET "https://api.telegram.org/bot7665636304:AAEsWwMX7QG4tVoC3IufpSjL-ZMjfspIphY/getWebhookInfo"
curl -X POST https://web-production-6698.up.railway.app/webhook -d '{"update_id":123456,"message":{"message_id":1,"from":{"id":12345678,"is_bot":false,"first_name":"Test"},"chat":{"id":12345678,"first_name":"Test","type":"private"},"date":1700000000,"text":"/start"}}' -H "Content-Type: application/json"
curl -X POST "https://api.telegram.org/bot7665636304:AAEsWwMX7QG4tVoC3IufpSjL-ZMjfspIphY/deleteWebhook"
curl -X POST "https://api.telegram.org/bot7665636304:AAEsWwMX7QG4tVoC3IufpSjL-ZMjfspIphY/setWebhook?url=https://web-production-6698.up.railway.app/webhook"
curl -X POST https://web-production-6698.up.railway.app/webhook -d '{"update_id":123456,"message":{"message_id":1,"from":{"id":12345678,"is_bot":false,"first_name":"Test"},"chat":{"id":12345678,"first_name":"Test","type":"private"},"date":1700000000,"text":"/start"}}' -H "Content-Type: application/json"
curl -X GET "https://api.telegram.org/bot7665636304:AAEsWwMX7QG4tVoC3IufpSjL-ZMjfspIphY/getWebhookInfo"
curl -X POST https://web-production-6698.up.railway.app/webhook -d '{"update_id":123456,"message":{"message_id":1,"from":{"id":12345678,"is_bot":false,"first_name":"Test"},"chat":{"id":12345678,"first_name":"Test","type":"private"},"date":1700000000,"text":"/start"}}' -H "Content-Type: application/json"
curl "https://api.telegram.org/7665636304:AAEsWwMX7QG4tVoC3IufpSjL-ZMjfspIphY/getUpdates"
curl "https://api.telegram.org/bot7665636304:AAEsWwMX7QG4tVoC3IufpSjL-ZMjfspIphY/deleteWebhook?drop_pending_updates=True"
curl -X POST "https://api.telegram.org/bot7665636304:AAEsWwMX7QG4tVoC3IufpSjL-ZMjfspIphY/setWebhook" -d "url=https://web-production-6698.up.railway.app/webhook&allowed_updates=[\"message\",\"edited_message\",\"channel_post\",\"edited_channel_post\",\"message_reaction\",\"chat_member\"]"
curl "https://api.telegram.org/bot7665636304:AAEsWwMX7QG4tVoC3IufpSjL-ZMjfspIphY/getWebhookInfo"
curl "https://api.telegram.org/bot7665636304:AAEsWwMX7QG4tVoC3IufpSjL-ZMjfspIphY/getUpdates"
curl "https://api.telegram.org/bot7665636304:AAEsWwMX7QG4tVoC3IufpSjL-ZMjfspIphY/deleteWebhook?drop_pending_updates=True"
curl -X POST "https://api.telegram.org/bot7665636304:AAEsWwMX7QG4tVoC3IufpSjL-ZMjfspIphY/setWebhook" -d "url=https://web-production-6698.up.railway.app/webhook&allowed_updates=[\"message\",\"edited_message\",\"channel_post\",\"edited_channel_post\",\"message_reaction\"]"
curl "https://api.telegram.org/bot7665636304:AAEsWwMX7QG4tVoC3IufpSjL-ZMjfspIphY/getUpdates"
