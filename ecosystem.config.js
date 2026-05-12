module.exports = {
  apps: [
    {
      name: 'bond-backend',
      cwd: './backend',
      script: './venv/bin/python3',
      args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8504',
      env: {
        NODE_ENV: 'production',
      },
    },
    {
      name: 'bond-frontend',
      cwd: './frontend',
      script: 'npm',
      args: 'run preview -- --port 8503 --host 0.0.0.0',
      env: {
        NODE_ENV: 'production',
      },
    },
  ],
};
