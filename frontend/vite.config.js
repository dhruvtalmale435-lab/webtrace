import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
export default defineConfig({plugins:[react()],server:{host:'127.0.0.1',proxy:{'/api':'http://127.0.0.1:8000','/health':'http://127.0.0.1:8000','/demo':'http://127.0.0.1:8000','/screenshots':'http://127.0.0.1:8000'}},build:{rollupOptions:{output:{manualChunks:{charts:['recharts'],motion:['motion/react'],router:['react-router-dom']}}}}})
