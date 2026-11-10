# EC2 deployment guide for this Django project

This guide shows the complete process from GitHub Secrets to the final live deployment on an AWS EC2 instance using Gunicorn, PM2, and Nginx.

## 1) Prepare the EC2 server

Launch an Ubuntu EC2 instance and connect to it:

```bash
ssh ubuntu@<EC2_HOST>
```

Install the required packages:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git nginx curl
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g pm2
```

Create the app directory:

```bash
cd /home/ubuntu
git clone <YOUR_GITHUB_REPO_URL> chetanshop
cd chetanshop
```

Create the Python environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Create the environment file from the template:

```bash
cp .env.example .env
nano .env
```

Fill in real values for the production environment. Use your real domain or EC2 public IP in `ALLOWED_HOSTS` and a strong random value for `SECRET_KEY`.

Example:

```env
SECRET_KEY=your-very-long-random-secret
DEBUG=False
ALLOWED_HOSTS=example.com,www.example.com,<EC2_HOST>
DATABASE_URL=postgresql://user:password@db-host:5432/dbname
SECURE_SSL_REDIRECT=False
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_REGION_NAME=
```

If you are using SQLite only for testing, you can keep the default local file, but for production on EC2 it is better to use PostgreSQL.

Now run the Django setup once:

```bash
source .venv/bin/activate
python manage.py collectstatic --noinput
python manage.py migrate --noinput
```

Start the app with PM2 using the project config:

```bash
pm2 start ecosystem.config.js
pm2 save
```

Configure Nginx:

```bash
sudo cp deploy/nginx.conf /etc/nginx/conf.d/chetanshop.conf
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

Make sure the domain name or public IP points to this EC2 instance and that `ALLOWED_HOSTS` includes it.

---

## 2) Add GitHub Secrets

Open your GitHub repository, then go to:

Settings → Secrets and variables → Actions → New repository secret

Add these exact secrets:

- `EC2_HOST`
- `EC2_USERNAME`
- `EC2_SSH_KEY`

Example values:
- `EC2_HOST` = `13.234.56.78`
- `EC2_USERNAME` = `ubuntu`
- `EC2_SSH_KEY` = the private key content for the EC2 key pair

Do not commit secrets to the repo. Store them only in GitHub Secrets.

---

## 3) GitHub Actions deployment workflow

The workflow file at [.github/workflows/deploy.yml](.github/workflows/deploy.yml) is triggered when code is pushed to the `main` branch.

It does the following:

1. Checks out the latest code
2. Creates an SSH connection to the EC2 machine
3. Uses the EC2 key from GitHub Secrets
4. Runs the deployment script on the server

The deployment command is:

```bash
ssh -i ~/.ssh/ec2_key -o StrictHostKeyChecking=yes "${{ secrets.EC2_USERNAME }}@${{ secrets.EC2_HOST }}" "bash -lc 'cd /home/ubuntu/chetanshop && bash deploy/deploy.sh'"
```

This is how automatic deployment is triggered on every push to `main`.

---

## 4) Deployment script behavior

The script at [deploy/deploy.sh](deploy/deploy.sh) does the following on the server:

```bash
#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/home/ubuntu/chetanshop"
VENV_DIR="$APP_DIR/.venv"

cd "$APP_DIR"

git fetch --all
if git rev-parse --verify main >/dev/null 2>&1; then
  git checkout main
  git pull --ff-only origin main
else
  git pull --ff-only origin master
fi

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
pm2 startOrReload ecosystem.config.js --update-env
pm2 save
```

This ensures the latest code is pulled, dependencies are installed, static files are generated, migrations are applied, and PM2 restarts the Gunicorn app cleanly.

---

## 5) PM2 + Gunicorn process configuration

The file [ecosystem.config.js](ecosystem.config.js) tells PM2 to run Gunicorn for the Django app:

```js
module.exports = {
  apps: [
    {
      name: 'manglam-furniture',
      cwd: '/home/ubuntu/chetanshop',
      script: 'gunicorn',
      args: 'manglam_furniture.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120',
      interpreter: '/home/ubuntu/chetanshop/.venv/bin/python',
      exec_mode: 'fork',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        DJANGO_SETTINGS_MODULE: 'manglam_furniture.settings.production',
        PORT: '8000'
      }
    }
  ]
};
```

This gives you automatic restarts if the app crashes or the server reboots.

---

## 6) Nginx reverse proxy

The file [deploy/nginx.conf](deploy/nginx.conf) configures Nginx to:

- serve files from `/static/` and `/media/` directly
- proxy everything else to the local Gunicorn app at `127.0.0.1:8000`
- forward real client IP and host headers to Django

This is the standard production pattern for Django behind Nginx.

---

## 7) Final deployment steps

After the server is ready and the GitHub secrets are added:

1. Push the code to the `main` branch.
2. GitHub Actions will run the deployment workflow.
3. The workflow will SSH into the EC2 instance.
4. The server will run [deploy/deploy.sh](deploy/deploy.sh).
5. PM2 will reload Gunicorn.
6. Nginx will serve the app.

Verify the site by opening the server URL in the browser:

```bash
http://<EC2_HOST>
```

If HTTPS is configured, use your domain instead:

```bash
https://example.com
```

---

## 8) Optional HTTPS with Certbot

For secure production deployment, enable HTTPS:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d example.com -d www.example.com
```

Then restart Nginx and confirm the site loads over HTTPS.

---

## 9) Useful production checks

Check PM2 status:

```bash
pm2 status
```

Check logs:

```bash
pm2 logs manglam-furniture
```

Check Nginx status:

```bash
sudo systemctl status nginx
```

Check Django app health:

```bash
curl http://127.0.0.1:8000
```

If the app is not responding correctly, review the PM2 logs and the Nginx config, then fix the issue and redeploy by pushing to `main` again.

---

## 10) Required GitHub secrets summary

The repository needs these secrets configured in GitHub:

- `EC2_HOST`
- `EC2_USERNAME`
- `EC2_SSH_KEY`

This gives you a complete GitHub-to-EC2 auto-deploy flow for this Django project.
