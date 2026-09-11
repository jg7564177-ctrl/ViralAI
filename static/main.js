document.addEventListener('DOMContentLoaded', () => {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js').catch(() => {});
  }

  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const chatBox = document.getElementById('chat-box');
  const scenarioForm = document.getElementById('scenario-form');
  const analysisForm = document.getElementById('analysis-form');
  const projectsList = document.getElementById('projects-list');
  const assistantThinking = document.getElementById('assistant-thinking');
  const splashScreen = document.getElementById('splash-screen');
  const progressPanel = document.getElementById('generation-progress');
  const progressFill = document.getElementById('progress-fill');
  const progressLabel = document.getElementById('progress-label');
  const progressSteps = Array.from(document.querySelectorAll('.progress-steps li'));
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const createPrompt = document.getElementById('create-prompt');
  const promptCounter = document.getElementById('prompt-counter');
  const clearPromptBtn = document.getElementById('clear-prompt-btn');
  const improvePromptBtn = document.getElementById('improve-prompt-btn');
  const generateBtn = document.getElementById('generate-btn');
  const advancedToggle = document.getElementById('advanced-toggle');
  const advancedPanel = document.getElementById('advanced-panel');
  const addSceneBtn = document.getElementById('add-scene-btn');
  const storyboardList = document.getElementById('storyboard-list');
  const createScreen = document.getElementById('create-screen');
  const conversationList = document.getElementById('conversation-list');
  const newConversationBtn = document.getElementById('new-conversation-btn');
  const stopGenerationBtn = document.getElementById('stop-generation-btn');
  const userId = 'demo';
  let activeConversationId = null;
  let currentAbortController = null;

  const createConversation = async (title = 'Nouvelle conversation') => {
    const response = await fetch('/api/chat/conversations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-User-Id': userId },
      body: JSON.stringify({ title }),
    });
    const payload = await response.json();
    if (!payload.conversation) return null;
    activeConversationId = payload.conversation.id;
    renderConversationList();
    renderConversation(payload.conversation);
    return payload.conversation;
  };

  const renderConversationList = async () => {
    if (!conversationList) return;
    const response = await fetch('/api/chat/conversations', { headers: { 'X-User-Id': userId } });
    const payload = await response.json();
    const conversations = payload.conversations || [];
    conversationList.innerHTML = '';

    conversations.forEach((conversation) => {
      const item = document.createElement('button');
      item.type = 'button';
      item.className = `conversation-item ${conversation.id === activeConversationId ? 'active' : ''}`;
      item.innerHTML = `
        <strong>${conversation.title || 'Nouvelle conversation'}</strong>
        <small>${conversation.messages?.length || 0} messages</small>
      `;
      item.addEventListener('click', async () => {
        activeConversationId = conversation.id;
        const convoResponse = await fetch(`/api/chat/conversations/${conversation.id}`, { headers: { 'X-User-Id': userId } });
        const convoPayload = await convoResponse.json();
        if (convoPayload.conversation) {
          renderConversation(convoPayload.conversation);
        }
        renderConversationList();
      });
      conversationList.appendChild(item);
    });
  };

  const renderConversation = (conversation) => {
    if (!chatBox) return;
    chatBox.innerHTML = '';
    (conversation.messages || []).forEach((message) => {
      const messageEl = document.createElement('div');
      messageEl.className = `message ${message.role === 'user' ? 'user' : 'bot'}`;
      messageEl.textContent = message.content;
      chatBox.appendChild(messageEl);

      if (message.role === 'assistant') {
        const actionRow = document.createElement('div');
        actionRow.className = 'assistant-actions';
        actionRow.innerHTML = `
          <button type="button" class="mini-action" data-copy="${message.content}">Copier</button>
          <button type="button" class="mini-action" data-regenerate="${conversation.id}">Régénérer</button>
          <button type="button" class="mini-action" data-modify="${message.content}">Modifier</button>
          <button type="button" class="mini-action primary-action" data-video="${message.content}">🎬 Transformer en vidéo</button>
        `;
        actionRow.querySelectorAll('[data-copy]').forEach((btn) => {
          btn.addEventListener('click', async () => {
            try {
              await navigator.clipboard.writeText(btn.dataset.copy);
            } catch (error) {
              console.warn('Clipboard unavailable', error);
            }
          });
        });
        actionRow.querySelectorAll('[data-video]').forEach((btn) => {
          btn.addEventListener('click', async () => {
            const text = btn.dataset.video;
            if (!text) return;
            const response = await fetch('/api/chat/projects/from-message', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json', 'X-User-Id': userId },
              body: JSON.stringify({ idea: text, format: '9:16', duration: 15, style: 'cinematic' }),
            });
            const payload = await response.json();
            if (payload.project) {
              if (createPrompt) createPrompt.value = payload.project.prompt || text;
              const sceneList = document.getElementById('storyboard-list');
              if (sceneList && payload.project.storyboard) {
                sceneList.innerHTML = payload.project.storyboard.map((scene, index) => `
                  <article class="story-card">
                    <div class="story-card-header"><strong>Scène ${index + 1}</strong></div>
                    <p>${scene.description || 'Scène préparée'}</p>
                    <ul>
                      <li><span>Durée</span><strong>${scene.duration || 4}s</strong></li>
                      <li><span>Caméra</span><strong>${scene.camera_motion || 'tracking'}</strong></li>
                      <li><span>Transition</span><strong>${scene.transition || 'cut'}</strong></li>
                    </ul>
                  </article>
                `).join('');
              }
              if (createScreen) createScreen.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
          });
        });
        chatBox.appendChild(actionRow);
      }
    });
    chatBox.scrollTop = chatBox.scrollHeight;
  };

  const ensureConversation = async () => {
    if (!activeConversationId) {
      const created = await createConversation();
      if (created) activeConversationId = created.id;
    }
    await renderConversationList();
  };

  if (newConversationBtn) {
    newConversationBtn.addEventListener('click', async () => {
      activeConversationId = null;
      chatBox.innerHTML = '';
      await ensureConversation();
    });
  }

  if (stopGenerationBtn) {
    stopGenerationBtn.addEventListener('click', () => {
      if (currentAbortController) {
        currentAbortController.abort();
        currentAbortController = null;
      }
      setThinking(false);
    });
  }

  if (document.querySelectorAll('.preset-chip').length && chatInput) {
    document.querySelectorAll('.preset-chip').forEach((button) => {
      button.addEventListener('click', () => {
        const value = button.dataset.message || '';
        chatInput.value = value;
        chatInput.focus();
      });
    });
  }

  if (!prefersReducedMotion && splashScreen) {
    setTimeout(() => {
      splashScreen.classList.add('hidden');
    }, 900);
  } else if (splashScreen) {
    splashScreen.classList.add('hidden');
  }

  const addMessage = (text, role = 'bot') => {
    const messageEl = document.createElement('div');
    messageEl.className = `message ${role}`;
    messageEl.textContent = text;
    chatBox.appendChild(messageEl);
    chatBox.scrollTop = chatBox.scrollHeight;
  };

  const setThinking = (active) => {
    if (!assistantThinking) return;
    assistantThinking.classList.toggle('hidden', !active);
  };

  if (createPrompt && promptCounter) {
    const syncPromptCounter = () => {
      const length = createPrompt.value.length;
      promptCounter.textContent = `${length} / 500`;
    };
    createPrompt.addEventListener('input', syncPromptCounter);
    syncPromptCounter();
  }

  if (clearPromptBtn && createPrompt) {
    clearPromptBtn.addEventListener('click', () => {
      createPrompt.value = '';
      if (promptCounter) promptCounter.textContent = '0 / 500';
      createPrompt.focus();
    });
  }

  if (improvePromptBtn && createPrompt) {
    improvePromptBtn.addEventListener('click', () => {
      const base = createPrompt.value.trim() || 'Un personnage futuriste marche dans une ville cyberpunk sous la pluie, caméra cinématique, éclairages néon.';
      const improved = base.replace(/\s+/g, ' ').trim() + ', composition dynamique, plans immersifs, lumière dramatique, punchy, vertical format.';
      createPrompt.value = improved;
      if (promptCounter) promptCounter.textContent = `${createPrompt.value.length} / 500`;
    });
  }

  if (generateBtn) {
    generateBtn.addEventListener('click', () => {
      const text = createPrompt ? createPrompt.value.trim() : '';
      if (!text) {
        alert('Rédige un prompt pour lancer la création.');
        return;
      }
      alert('Génération bientôt disponible');
    });
  }

  if (advancedToggle && advancedPanel) {
    advancedToggle.addEventListener('click', () => {
      advancedPanel.classList.toggle('hidden');
      advancedToggle.textContent = advancedPanel.classList.contains('hidden') ? 'Options avancées' : 'Masquer les options avancées';
    });
  }

  if (addSceneBtn && storyboardList) {
    addSceneBtn.addEventListener('click', () => {
      const index = storyboardList.children.length + 1;
      const scene = document.createElement('article');
      scene.className = 'story-card';
      scene.innerHTML = `
        <div class="story-card-header"><strong>Scène ${index}</strong></div>
        <p>Nouvelle scène préparée pour le storyboard.</p>
        <ul>
          <li><span>Durée</span><strong>4s</strong></li>
          <li><span>Caméra</span><strong>tracking</strong></li>
          <li><span>Transition</span><strong>cut</strong></li>
        </ul>
      `;
      storyboardList.appendChild(scene);
    });
  }

  if (createScreen) {
    createScreen.dataset.ready = 'true';
  }

  if (chatForm) {
    chatForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const message = chatInput.value.trim();
      if (!message) return;

      addMessage(message, 'user');
      chatInput.value = '';
      setThinking(true);

      try {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message }),
        });

        const payload = await response.json();
        setThinking(false);
        addMessage(payload.response || 'Je vais travailler sur ce concept.', 'bot');
      } catch (error) {
        setThinking(false);
        addMessage('Je n’ai pas pu contacter l’assistant pour le moment.', 'bot');
      }
    });
  }

  if (scenarioForm) {
    scenarioForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      if (progressPanel) {
        progressPanel.classList.remove('hidden');
      }

      const payload = {
        description: document.getElementById('description').value,
        duration: Number(document.getElementById('duration').value || 20),
        format: document.getElementById('format').value,
        style: document.getElementById('style').value,
        music: document.getElementById('music').value,
        voice: document.getElementById('voice').value,
        subtitles: document.getElementById('subtitles').checked,
        quality: document.getElementById('quality').value,
      };

      const steps = [
        '🧠 Préparation de ton idée...',
        '🎬 Génération des scènes...',
        '✨ Assemblage...',
        '✅ Vidéo terminée',
      ];

      const updateProgress = (index, message) => {
        if (progressLabel) {
          progressLabel.textContent = message;
        }
        progressSteps.forEach((step, i) => {
          step.classList.toggle('active', i <= index);
        });
        if (progressFill) {
          progressFill.style.width = `${((index + 1) / steps.length) * 100}%`;
        }
      };

      updateProgress(0, steps[0]);

      try {
        const aiResponse = await fetch('/api/ai/brain', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: payload.description, mode: payload.style || 'general' }),
        });
        const aiData = await aiResponse.json();
        updateProgress(1, steps[1]);

        const jobResponse = await fetch('/api/video/jobs', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            description: payload.description,
            duration: payload.duration,
            format: payload.format,
            style: payload.style,
            mode: payload.style || 'general',
          }),
        });
        const jobData = await jobResponse.json();

        updateProgress(2, steps[2]);

        const resultContainer = document.createElement('div');
        resultContainer.className = 'analysis-result';
        resultContainer.innerHTML = `
          <h4>${aiData.title || 'Concept généré'}</h4>
          <p><strong>Hook:</strong> ${aiData.hook || 'À définir'}</p>
          <p><strong>Script:</strong> ${aiData.script || 'À définir'}</p>
          <p><strong>Statut du job:</strong> ${jobData.status || 'QUEUED'}</p>
          <p><strong>Message:</strong> ${jobData.message || 'Traitement en cours'}</p>
          <ul>
            ${(aiData.scenes || []).map((scene) => `<li>${scene.time} — ${scene.description}</li>`).join('')}
          </ul>
        `;

        const panel = scenarioForm.closest('.panel');
        const existing = panel.querySelector('.analysis-result');
        if (existing) existing.remove();
        panel.appendChild(resultContainer);

        if (jobData.status === 'VIDEO_PROVIDER_NOT_CONFIGURED') {
          updateProgress(3, '⚠️ Fournisseur vidéo non configuré');
          return;
        }

        if (jobData.job_id) {
          let attempts = 0;
          const pollJob = async () => {
            const statusResponse = await fetch(`/api/video/jobs/${jobData.job_id}`);
            const statusData = await statusResponse.json();
            const progressValue = Math.min(100, Math.max(35, statusData.progress || 30 + attempts * 10));
            if (progressFill) {
              progressFill.style.width = `${progressValue}%`;
            }
            if (statusData.status === 'COMPLETED') {
              updateProgress(3, steps[3]);
              return;
            }
            if (statusData.status === 'FAILED' || statusData.status === 'VIDEO_PROVIDER_NOT_CONFIGURED') {
              updateProgress(3, '⚠️ Génération impossible');
              return;
            }
            attempts += 1;
            if (attempts < 5) {
              setTimeout(pollJob, 800);
            } else {
              updateProgress(3, steps[3]);
            }
          };
          pollJob();
        } else {
          updateProgress(3, steps[3]);
        }
      } catch (error) {
        updateProgress(3, '⚠️ Génération impossible');
        alert('Le scénario n’a pas pu être généré.');
      }
    });
  }

  if (analysisForm) {
    analysisForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const input = document.getElementById('video-file');
      const file = input.files[0];
      if (!file) {
        alert('Sélectionne une vidéo pour l’analyse.');
        return;
      }

      const formData = new FormData();
      formData.append('video', file);

      try {
        const response = await fetch('/api/analyze-video', {
          method: 'POST',
          body: formData,
        });

        const data = await response.json();
        const result = document.getElementById('analysis-result');
        if (!result) return;

        result.innerHTML = `
          <h4>${data.source_name}</h4>
          <div class="stats-grid" style="margin-top: 12px; grid-template-columns: repeat(2, minmax(120px, 1fr));">
            <div class="stat-card">
              <span>Accroche</span>
              <strong>82%</strong>
            </div>
            <div class="stat-card">
              <span>Rétention</span>
              <strong>74%</strong>
            </div>
            <div class="stat-card">
              <span>Montage</span>
              <strong>68%</strong>
            </div>
            <div class="stat-card">
              <span>Viral</span>
              <strong>77%</strong>
            </div>
          </div>
          <p style="margin-top: 16px;"><strong>Durée:</strong> ${data.duration_seconds}s</p>
          <p><strong>Rythme:</strong> ${data.rhythm}</p>
          <p><strong>Premières secondes:</strong> ${data.first_seconds}</p>
          <p><strong>Pourquoi ça a peu marché:</strong> ${data.reasons.join(' ')}</p>
          <ul>
            ${data.recommendations.map((item) => `<li>${item}</li>`).join('')}
          </ul>
        `;
      } catch (error) {
        alert('L’analyse de la vidéo a échoué.');
      }
    });
  }

  if (projectsList) {
    fetch('/api/projects')
      .then((res) => res.json())
      .then((data) => {
        if (!data.projects || !data.projects.length) return;
        projectsList.innerHTML = data.projects.map((project) => `
          <div class="project-card">
            <strong>${project.name}</strong>
            <span>${project.type}</span>
            <em>${project.status}</em>
          </div>
        `).join('');
      })
      .catch(() => {
        projectsList.innerHTML = '<div class="project-card"><strong>Projets</strong><span>Chargement local</span></div>';
      });
  }
});
