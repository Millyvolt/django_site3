# PostgreSQL Migration Guide

This guide explains how to migrate from SQLite to PostgreSQL for production deployment on Amvera.

## Overview

The application now supports PostgreSQL for production while keeping SQLite for local development. The database configuration automatically detects which database to use based on environment variables.

## Local Development

**No changes needed!** The application will continue using SQLite locally when `DATABASE_URL` is not set.

## Production Setup on Amvera

### Step 1: Add PostgreSQL Service

1. Log in to your Amvera dashboard
2. Navigate to your project settings
3. Add a PostgreSQL database service/addon
4. Note the connection details provided by Amvera

### Step 2: Configure Environment Variables

In your Amvera project settings, add the `DATABASE_URL` environment variable:

**Option A: Using DATABASE_URL (Recommended)**
```
DATABASE_URL=postgresql://username:password@host:port/database_name
```

Example:
```
DATABASE_URL=postgresql://myuser:mypassword@db.example.com:5432/mydb
```

**Option B: Using Individual Variables**
If Amvera doesn't provide a connection string, you can set individual variables:
```
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=your_host
DB_PORT=5432
```

### Step 3: Deploy and Run Migrations

After setting the environment variables:

1. Deploy your application to Amvera
2. The application will automatically connect to PostgreSQL
3. Run migrations to create tables:
   ```bash
   python manage.py migrate
   ```
4. Create the cache table:
   ```bash
   python manage.py createcachetable
   ```
5. Create a superuser (if needed):
   ```bash
   python manage.py createsuperuser
   ```

### Step 4: Migrate Existing Data (Optional)

If you have existing data in SQLite that you want to migrate:

1. **Export data from SQLite:**
   ```bash
   python manage.py dumpdata --exclude auth.permission --exclude contenttypes > data.json
   ```

2. **After setting up PostgreSQL and running migrations, import data:**
   ```bash
   python manage.py loaddata data.json
   ```

**Note:** Make sure to run migrations first before importing data!

## Verification

To verify PostgreSQL is working:

1. Check the application logs - you should see successful database connections
2. Try accessing the admin panel - it should work without "database is locked" errors
3. Test creating/editing workout sessions - operations should be fast and reliable

## Troubleshooting

### Connection Errors

If you see connection errors:
- Verify `DATABASE_URL` is set correctly in Amvera
- Check that the PostgreSQL service is running
- Verify network access between your app and database

### Migration Errors

If migrations fail:
- Make sure you've run `python manage.py migrate` after setting up PostgreSQL
- Check that the database user has proper permissions
- Verify the database name exists

### Cache Table Issues

If cache operations fail:
- Run `python manage.py createcachetable` after migrations
- The cache table will be created in PostgreSQL automatically

## Benefits

✅ **Solves "database is locked" errors** - PostgreSQL handles concurrent access much better  
✅ **Better performance** - Optimized for production workloads  
✅ **Scalability** - Can handle many simultaneous connections  
✅ **Data integrity** - Better transaction support  
✅ **Cache efficiency** - Database cache works great with PostgreSQL  

## Rollback

If you need to rollback to SQLite temporarily:
1. Remove or unset the `DATABASE_URL` environment variable in Amvera
2. Redeploy the application
3. The app will automatically fall back to SQLite

**Warning:** This will use a fresh SQLite database - your PostgreSQL data won't be accessible.

