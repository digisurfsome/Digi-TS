# Railway Deployment Guide for Design Tree Studio

This guide explains how to deploy Design Tree Studio on Railway.

## Prerequisites

1. A Railway account (sign up at https://railway.app)
2. Your Design Tree Studio repository pushed to GitHub
3. An OpenAI API key

## Files Configured for Railway

The following files have been added/configured for Railway deployment:

- **Procfile** - Defines the web process command
- **railway.json** - Railway-specific configuration
- **runtime.txt** - Specifies Python version (3.11)
- **.streamlit/config.toml** - Streamlit server configuration
- **.railwayignore** - Files to exclude from deployment

## Deployment Steps

### 1. Create a New Railway Project

1. Go to https://railway.app and log in
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Authorize Railway to access your GitHub account
5. Select the `design-tree-studio` repository
6. Railway will automatically detect it's a Python app

### 2. Add PostgreSQL Database

1. In your Railway project, click "New" → "Database" → "Add PostgreSQL"
2. Railway will create a PostgreSQL instance and automatically set the `DATABASE_URL` variable
3. The database connection string is automatically available as `$DATABASE_URL`

**Important:** The app is already configured to use the `DATABASE_URL` environment variable.

### 3. Configure Environment Variables

In the Railway project settings, add these environment variables:

#### Required Variables:

```bash
OPENAI_API_KEY=sk-proj-your-openai-api-key-here
```

#### Optional Variables (already have defaults):

```bash
APP_NAME=Design Tree Studio
APP_VERSION=0.1.0
DEBUG=false
OPENAI_MODEL=gpt-4-turbo-preview
```

**Note:** `DATABASE_URL` is automatically set by Railway when you add the PostgreSQL service.

### 4. Deploy

1. Railway will automatically deploy when you connect the repo
2. Wait for the build and deployment to complete (usually 2-5 minutes)
3. Once deployed, Railway will provide a public URL (e.g., `your-app.railway.app`)

### 5. Initialize the Database

After the first deployment:

1. Visit your Railway app URL
2. Go to the "System Status" tab
3. Click "Initialize Schema" to create all database tables
4. The app is now ready to use!

## How the Configuration Works

### Procfile

```
web: streamlit run app/streamlit_app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
```

- Railway automatically sets the `$PORT` variable
- `--server.address=0.0.0.0` allows external connections
- `--server.headless=true` disables browser auto-open

### railway.json

Configures Railway to:
- Use Nixpacks builder (automatic Python setup)
- Restart on failure (max 10 retries)

### .streamlit/config.toml

Streamlit-specific settings:
- Runs in headless mode
- Disables CORS (Railway handles this)
- Disables usage stats collection

## Monitoring and Logs

1. **View Logs:** Click on your deployment in Railway → "Deployments" → View logs
2. **Check Status:** Monitor CPU, memory, and network usage in the Railway dashboard
3. **Database:** View database metrics in the PostgreSQL service tab

## Database Backups

Railway automatically backs up your PostgreSQL database. To manually export:

1. Go to the PostgreSQL service in Railway
2. Click "Connect" to get connection details
3. Use `pg_dump` or a tool like pgAdmin to export

## Troubleshooting

### Deployment Fails

- **Check logs** in Railway dashboard for error messages
- Verify all environment variables are set correctly
- Ensure `requirements.txt` is up to date

### Database Connection Errors

- Verify the PostgreSQL service is running in Railway
- Check that `DATABASE_URL` is automatically set (it should be)
- Ensure the app can reach the database (Railway handles this automatically)

### App Won't Start

- Check that the `Procfile` exists and has correct syntax
- Verify Python version in `runtime.txt` matches your app (3.11)
- Check Streamlit port configuration in `.streamlit/config.toml`

### Schema Initialization Fails

- Make sure the database is running
- Check database logs in Railway
- Verify all model definitions in `app/core/models.py` are correct

## Custom Domain (Optional)

To use your own domain:

1. Go to your Railway project settings
2. Click "Settings" → "Domains"
3. Click "Add Custom Domain"
4. Follow Railway's instructions to configure DNS

## Scaling

Railway automatically handles scaling based on your plan:

- **Hobby Plan:** Basic resources, good for development
- **Pro Plan:** More resources and custom domains
- **Team Plan:** Higher limits and team collaboration

## Cost Estimates

- **PostgreSQL:** Included in Railway plans
- **App hosting:** Based on usage (typically $5-20/month for small apps)
- **Free tier:** $5 of usage per month included

## Security Best Practices

1. ✅ **Never commit `.env`** - Environment variables are set in Railway dashboard
2. ✅ **Use PIN lock** - Configure in Settings tab after deployment
3. ✅ **HTTPS enabled** - Railway automatically provides SSL certificates
4. ✅ **Database encryption** - Railway's PostgreSQL uses encrypted connections
5. ⚠️ **Rotate API keys** - Change your OpenAI API key periodically

## Updating the Application

Railway automatically redeploys when you push to GitHub:

1. Make changes locally
2. Commit and push to GitHub
3. Railway detects the push and redeploys automatically
4. Monitor the deployment in Railway dashboard

## Environment-Specific Configuration

The app automatically adapts to Railway:

- Uses `$PORT` from Railway (not hardcoded)
- Uses `$DATABASE_URL` from PostgreSQL service
- Runs in production mode (headless)
- Uses environment variables from Railway settings

## Next Steps After Deployment

1. ✅ Visit your Railway app URL
2. ✅ Initialize database schema in System Status tab
3. ✅ Create your first user (automatic on first visit)
4. ✅ Create your first project
5. ✅ Configure OpenAI settings in Settings tab
6. ✅ Set a PIN code for security (optional but recommended)
7. ✅ Start using Design Tree Studio!

## Support and Resources

- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway
- **Design Tree Studio Issues:** https://github.com/digisurfsome/design-tree-studio/issues

## Quick Deploy Checklist

- [ ] Push code to GitHub
- [ ] Create Railway project from GitHub repo
- [ ] Add PostgreSQL database service
- [ ] Set `OPENAI_API_KEY` environment variable
- [ ] Wait for deployment to complete
- [ ] Visit app URL
- [ ] Initialize database schema
- [ ] Create first project
- [ ] Start building!

---

**You're all set!** Railway will handle the infrastructure, scaling, and SSL certificates automatically.
