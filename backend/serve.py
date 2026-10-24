"""Container entrypoint: keep server and bundled-demo ports in sync."""
import os
import uvicorn

def main():
    port = int(os.getenv('PORT', os.getenv('WEBTRACE_PORT', '8000')))
    os.environ['WEBTRACE_PORT'] = str(port)
    uvicorn.run('backend.main:app', host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()
