# 🏗️ Build Image

Scripts for building and pushing the Statechecker Docker image.

## 📋 Usage

### Linux/Mac
```bash
./build-image.sh
```

### Windows
```powershell
.\build-image.ps1
```

Run the script directly to choose the image name and version interactively. To provide both values without another prompt:

```powershell
.\build-image.ps1 -ImageName 'sokrates1989/statechecker' -ImageVersion '3.1.1'
```

Quick Start option 6 passes its selected name and version to this script, so the version is entered only once.

## 🔧 Process

The build script will:
1. Prompt for Docker image name and version
2. Build the Docker image from the project Dockerfile
3. Optionally push to a container registry
4. Update `.env` with the new image name/version

## 📦 Image Details

The built image contains:
- Python 3.13 base
- FastAPI application (API service)
- Website/tool/backup checker logic
- Database connectivity (MySQL)
- Telegram and email notification support

## 🚀 Deployment

After building and pushing the image, deploy to Docker Swarm using the [swarm-statechecker](https://github.com/Sokrates1989/swarm-statechecker) repository.
