# Vercel Deployment Configuration Guide

## Project Structure

This is a monorepo with:
- **Frontend**: Next.js app in `frontend/` directory
- **Backend**: Python FastAPI serverless functions in `api/` directory

## Vercel Dashboard Settings

### Root Directory
**DO NOT SET** a root directory in the Vercel dashboard. Leave it empty or set to `/` (project root).

**Why?** The `api/` directory must be accessible at the project root for Python serverless functions to work. If you set root directory to `frontend`, Vercel won't be able to find the Python functions.

### Framework Preset
Set to **"Next.js"** or **"Other"** (doesn't matter since we're overriding build commands).

### Build Command
```
cd frontend && npm install && npm run build
```

### Output Directory
```
frontend/.next
```

### Install Command
```
cd frontend && npm install
```

## vercel.json Configuration

The `vercel.json` file handles:
- Build commands (already configured)
- API route rewrites (routes `/api/*` to Python functions)
- Python function runtime settings

## Python Function Configuration

The Python serverless function is configured in `vercel.json`:

```json
"functions": {
  "api/index.py": {
    "runtime": "python3.11",
    "maxDuration": 60,
    "memory": 3008
  }
}
```

**Settings:**
- **Runtime**: Python 3.11
- **Max Duration**: 60 seconds (for data fetching)
- **Memory**: 3008 MB (Pro plan) - helps with pandas operations

## Environment Variables

Set these in Vercel Dashboard → Settings → Environment Variables:

### Required for Vercel Blob Storage:
- `BLOB_READ_WRITE_TOKEN` - Your Vercel Blob read/write token
- `BLOB_STORE_ID` - Your Vercel Blob store ID

### Optional:
- `NYC_API_APP_TOKEN` - NYC Open Data API token (increases rate limits)
- `CORS_ORIGINS` - Comma-separated list of allowed origins (defaults to localhost)

## How It Works

1. **Frontend Build**: Vercel runs the build command which builds the Next.js app in `frontend/`
2. **Python Functions**: Vercel automatically detects Python files in the `api/` directory
3. **API Routing**: The rewrite rule routes all `/api/*` requests to `/api/index.py`
4. **Caching**: Inspection data is cached in Vercel Blob storage (not local files)

## Troubleshooting

### If Python functions aren't detected:
- Ensure `api/index.py` exists at the project root
- Check that `rootDirectory` is NOT set to `frontend` in dashboard
- Verify `vercel.json` has the correct function configuration

### If build fails:
- Check that `frontend/package.json` exists
- Verify Node.js version compatibility
- Check build logs for specific errors

### If API routes return 404:
- Verify the rewrite rule in `vercel.json`
- Check that `api/index.py` exports the FastAPI `app`
- Ensure Python dependencies are in `api/requirements.txt`

## File Size Considerations

- **No parquet files**: We use JSON + Vercel Blob instead
- **No pyarrow**: Removed to reduce function size
- **Dependencies**: Only essential packages in `api/requirements.txt`
- **Data files**: CSV and JSON files are small and included in deployment

## Deployment Checklist

- [ ] Root directory is NOT set to `frontend` (or is empty)
- [ ] Build command points to `frontend` directory
- [ ] Output directory is `frontend/.next`
- [ ] `BLOB_READ_WRITE_TOKEN` environment variable is set
- [ ] `BLOB_STORE_ID` environment variable is set
- [ ] `api/index.py` exists and exports FastAPI app
- [ ] `api/requirements.txt` contains all Python dependencies
- [ ] `api/data/` contains `food_orders.csv` and `restaurant_mapping.json`

