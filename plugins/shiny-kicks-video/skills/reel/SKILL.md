---
name: reel
description: Inicia la edición de un Reel de Shiny Kicks a partir del video que el usuario subió. Usar cuando el usuario escriba /reel o pida "edita este video para Reels".
---

Inicia el flujo del skill `shiny-kicks-video-reel` con el video adjunto:

1. Si no hay video adjunto, pide que lo suba y detente.
2. Pregunta el tema con AskUserQuestion (objetivo, oferta, CTA, audio).
3. Analiza el video y publica el storyboard para autorizar.
4. No edites nada hasta recibir la autorización explícita del usuario.
