Use docker service create the first time, then docker service update for changes.

1) Create the Caddyfile as a secret (or use a Docker “config” if it isn’t sensitive)

Secrets are immutable—updating means creating a new one and pointing the service at it.

# first time
docker secret create caddyfile ./Caddyfile

# Create the Caddy Service

docker service create \
  --name caddy \
  --publish 80:80 \
  --publish 443:443 \
  --secret source=caddyfile,target=Caddyfile \
  --mount type=volume,source=caddy_data,destination=/data \
  --mount type=volume,source=caddy_config,destination=/config \
  caddy:2 \
  caddy run --config /run/secrets/Caddyfile --adapter caddyfile

Notes:

We override the command so Caddy reads the secret file at /run/secrets/Caddyfile.

/data stores Let’s Encrypt certs; keep it a named volume so certs persist.

Start with --replicas 1 unless you have shared storage for /data.

3) Update later

If you change the Caddyfile:

# create a new secret (secrets are immutable)
docker secret create caddyfile_v2 ./Caddyfile

# update the service to use the new secret and remove the old
docker service update \
  --secret-rm caddyfile \
  --secret-add source=caddyfile_v2,target=Caddyfile \
  caddy

If you only change the image or env, use docker service update --image caddy:2 (etc.).


