# PROJECT SPECIFICATIONS — Personal AI Operating System

> Inspiré de PASSION/PACT de DareDev256 (James), adapté au contexte personnel de Frederick.
>
> **Version :** 1.0 — Requirements Phase complete
> **Date de figement :** mai 2026
> **Auteur :** Frederick (alias Toufik)
> **Statut :** ✅ Requirements verrouillés, prêt pour les NFR puis l'architecture

---

## TABLE DES MATIÈRES

1. [Vision & Objectifs](#1-vision--objectifs)
2. [Scope du projet](#2-scope-du-projet)
3. [Décisions techniques](#3-décisions-techniques)
4. [Budget projet](#4-budget-projet)
5. [Concepts clés](#5-concepts-clés)
6. [User Stories — Brain Core (A)](#6-user-stories--brain-core-a)
7. [User Stories — Hevy Ingestion (B)](#7-user-stories--hevy-ingestion-b)
8. [User Stories — Analyse & Insights (C)](#8-user-stories--analyse--insights-c)
9. [User Stories — Coaching (D)](#9-user-stories--coaching-d)
10. [User Stories — Chat Coach (E)](#10-user-stories--chat-coach-e)
11. [User Stories — Gamification (F)](#11-user-stories--gamification-f)
12. [User Stories — Health Metrics](#12-user-stories--health-metrics)
13. [User Stories — Notifications](#13-user-stories--notifications)
14. [Modèles de données](#14-modèles-de-données)
15. [Données seed (programme d'entraînement)](#15-données-seed-programme-dentraînement)
16. [Récap MoSCoW global](#16-récap-moscow-global)

---

## 1. VISION & OBJECTIFS

### Vision

Un système d'**agent IA autonome et personnel** qui tourne 24/7 sur l'infrastructure self-hosted de Frederick (serveur i5 32GB Linux), qui l'assiste sur les domaines clés de sa vie (fitness, finance, carrière, code, social, journal de vie) en collectant des données depuis des APIs externes, en l'aidant à prendre des décisions, et en exécutant des tâches autonomes pendant qu'il dort ou est occupé.

### Objectifs

1. **Portfolio piece** pour le repositioning data eng / ML eng / agent engineering — un projet qui raconte une histoire et démontre la maîtrise de la stack moderne (LangGraph, MCP, RAG, MLOps).
2. **Outil d'usage quotidien réel** apportant de la valeur tangible (pas un projet vitrine).
3. **Terrain d'apprentissage** pour : Python en profondeur, LangGraph, agents autonomes, MCP, RAG, LLMOps, MLOps, observability, infra self-hosted.

### Utilisateur cible

**Frederick uniquement (single user)**. Pas de multi-user, pas de public, pas de SaaS. Simplification massive (pas de billing, multi-tenancy, RGPD complexe).

### Contraintes connues

- **Budget** : viser < 50€/mois en frais récurrents
- **Temps disponible** : 10-20h/semaine
- **Hébergement** : doit tourner sur serveur i5 32GB Linux existant
- **Sécurité** : zéro exposition publique non-protégée (Tailscale only ou auth forte)
- **Deadline** : aucune (priorité qualité)

---

## 2. SCOPE DU PROJET

### ✅ IN SCOPE — MVP (Phase 1 → Phase 3, ~3 mois)

- **Brain orchestrator** : boucle Think → Plan → Execute → Reflect
- **Mémoire long-terme persistante** (PostgreSQL + pgvector + RAG)
- **Dashboard web** Next.js pour interagir avec le système
- **1 agent : Fitness** complet avec intégration Hevy + Cronometer + suggestions + chat
- **Background jobs** (Celery + Redis) pour exécution autonome
- **Auth basique** (login + mot de passe) pour accéder au dashboard
- **Observability minimale** (logs structurés + dashboard de monitoring)
- **Déploiement self-hosted** sur i5 avec Caddy + Tailscale
- **Direct Line** : chat en temps réel avec l'agent (WebSocket)
- **Ingestion Health Connect** (sommeil, NEAT, HR via Tasker)
- **Saisie manuelle des prises de sang**
- **Notifications** : push (ntfy.sh) + email (Resend)
- **Gamification light** (streaks, missions, XP, niveaux)

### 🔜 IN SCOPE — Phase 4+ (post-MVP, mois 4-6+)

- Agent Career (job hunting auto)
- Agent Journal (entries texte → analyse + métriques)
- Agent Finance (intégrations BNP/Revolut + analyse)
- Agent Social (LinkedIn/Reddit/Twitter publication queue)
- Agent Code (multi-repos GitLab/GitHub management)
- Agent Intel (Reddit/HN/RSS aggregator)
- Self-improvement loop (l'agent apprend de ses erreurs)
- LLM routing (Claude/Gemini/Ollama selon contexte)
- Daily briefing automatique du matin
- Weekly boss / gamification avancée du dashboard
- **Google Calendar integration**
- **Polymarket** : recommandations only, ZÉRO trading auto
- **TTS** (text-to-speech)
- **CGM Dexcom auto-import** (via Cronometer ou xDrip+/Nightscout)
- **App Android Kotlin custom** pour Health Connect bridge plus robuste
- **Webhooks Hevy** (migration depuis polling)
- **Sync bidirectionnelle Hevy** (créer/modifier des workouts depuis l'agent)
- **MCP server custom** pour Hevy (passion-hevy-mcp) en Python

### ❌ OUT OF SCOPE — Won't Have

- ❌ App mobile native (web responsive seulement)
- ❌ Multi-utilisateur / partage public
- ❌ Trading automatique (peu importe quel marché)
- ❌ Reconnaissance vocale (STT)
- ❌ Génération d'images/vidéos par l'agent

---

## 3. DÉCISIONS TECHNIQUES

### Stack finale

| Couche | Technologie | Pourquoi |
|---|---|---|
| **Frontend** | Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui | Frederick connaît React, standard pro 2026 |
| **Backend** | FastAPI (Python 3.12+) + Pydantic v2 | Écosystème agent dominant en Python |
| **Agents** | LangGraph | Framework agent le plus solide en 2026 |
| **LLM principal** | Claude Sonnet 4.5 (API Anthropic) | Best pour code & tool use, MCP natif |
| **LLM fallback** | Claude Haiku / Gemini 2.5 Flash | Coûts maîtrisés pour tâches simples |
| **DB principale** | PostgreSQL 16+ avec pgvector | RAG intégré, JSONB pour flexibilité |
| **Cache + Queues** | Redis 7+ | BullMQ-like via Celery |
| **Jobs async** | Celery + Redis | Background tasks, scheduling |
| **Communication temps réel** | WebSocket (FastAPI native) | Dashboard live updates |
| **Auth** | NextAuth.js (front) + JWT (API) | Standard sécurisé |
| **Reverse Proxy** | Caddy | HTTPS auto, config ultra simple |
| **Containers** | Docker + docker-compose | Portabilité, repro |
| **Accès distant** | Tailscale (free tier perso) | Pas d'exposition publique |
| **Embeddings** | text-embedding-3-small (OpenAI) OU all-MiniLM-L6-v2 (local) | RAG vectoriel |

### Intégrations externes

| Service | Usage | Stratégie d'intégration |
|---|---|---|
| **Hevy Pro (lifetime $74.99)** | Workouts tracking | `hevy-mcp` (chrisdoc) en MCP, polling toutes les 30 min |
| **Cronometer Gold (~5€/mois)** | Nutrition tracking | `cronometer-mcp` (community), sync horaire |
| **ntfy.sh** | Push notifications mobile | HTTP POST vers topic personnel |
| **Resend** | Emails (briefing matinal) | Free tier 3000 emails/mois |
| **Tasker + AutoHealth Connect** | Bridge Health Connect → API | Push horaire vers `/api/v1/health/ingest` |
| **Anthropic API** | LLM principal | Sonnet 4.5 + Haiku selon contexte |

### Hébergement

- **Serveur i5 32GB Linux existant** (Frederick l'a déjà)
- **Pas de Mac Mini M4** (économie de 700-900€)
- **Pas de cloud VPS** pour le MVP (Hetzner en fallback potentiel)

### Stratégie d'intégration "build vs buy"

- **buy** : tout ce qui n'est pas différenciateur (hevy-mcp, cronometer-mcp, Resend, ntfy, etc.)
- **build** : le brain orchestrator, les agents custom, la logique métier, le dashboard

### Plan de migration Phase 4+

- `hevy-mcp` (Node.js, community) → `passion-hevy-mcp` (Python, custom)
- Polling Hevy → Webhooks Hevy
- Tasker + AutoHealth Connect → App Android Kotlin custom
- Saisie manuelle CGM → Auto-import via Cronometer ou xDrip+

---

## 4. BUDGET PROJET

### Coût mensuel récurrent estimé

```
Anthropic API (Claude)              : 20-40€
Cronometer Gold (annuel)            :  ~5€
Resend (3000 emails free tier)      :   0€
ntfy.sh                             :   0€
Tailscale (free tier perso)         :   0€
Électricité i5 24/7                 : 5-10€
Domaine optionnel                   :  ~1€
─────────────────────────────────────────
TOTAL                              : 31-56€/mois
```

### Coûts one-time

```
Hevy Pro Lifetime                   : ~70€ (amorti ~2€/mois sur 3 ans)
Tasker (Play Store)                 :  ~4€
AutoHealth Connect plugin           :  ~3€
─────────────────────────────────────────
TOTAL                              :  ~77€
```

### Coûts évités

- Mac Mini M4 : -700 à -900€
- VPS cloud type Railway : -10 à -30€/mois
- Apple Developer Account (pas d'app iOS) : -99€/an

---

## 5. CONCEPTS CLÉS

### Agent IA autonome (vs chatbot)

Un **agent** est un système capable de :
- Décider QUOI faire sans qu'on lui demande à chaque fois
- Utiliser des outils (appeler APIs, écrire code, lire fichiers)
- Planifier des étapes multiples pour atteindre un objectif
- Réfléchir sur ses erreurs et s'améliorer

Le brain tourne en boucle continue : **Think → Plan → Execute → Reflect**.

### MCP (Model Context Protocol)

Protocole créé par Anthropic en novembre 2024 qui standardise comment un LLM se connecte à des outils externes et à de la mémoire. C'est l'USB-C des LLMs. Un **MCP server** expose des outils/données ; un **MCP client** les consomme. Notre brain sera un MCP client.

### Mémoire long-terme + RAG

- Stockage de tout ce que l'agent a vu/fait (vector database : pgvector dans PostgreSQL)
- Retrieval Augmented Generation (RAG) pour retrouver les infos pertinentes
- Maintien d'un "état du monde" cohérent

### Multi-agent system

Au lieu d'un agent unique, plusieurs agents spécialisés collaborent (career, fitness, finance, social, code...). Framework choisi : **LangGraph**.

### Tool calling / function calling

Mécanisme par lequel le LLM appelle des fonctions de notre code. On déclare les fonctions disponibles, le LLM décide quoi appeler avec quels arguments.

### Background jobs / scheduling

Système exécutant des tâches périodiques 24/7 même sans interaction utilisateur. Implémentation : **Celery + Redis**.

### LLM local vs API

- **API** (Claude/GPT/Gemini) : performant, mais coûts par token et données externes
- **Local** (Ollama + Llama/Qwen) : gratuit, privé, mais nécessite GPU/CPU performant

Stratégie : Claude API au démarrage, migration partielle vers local en Phase 4+ pour les tâches simples (LLM routing).

### Observability

- **Logs structurés** (JSON, niveaux WARNING/ERROR/INFO/DEBUG)
- **Metrics** (appels LLM, latence, erreurs, coûts)
- **Traces** (raisonnement step-by-step de l'agent)
- **Alerting** (ntfy en cas de crash)

### Prompt Engineering structuré

La qualité d'une réponse LLM dépend à 80% du prompt. Structure type :
1. **System role** : qui est l'agent
2. **Contexte personnel** : phase, weight, kcal, sleep target, supplements...
3. **Contexte factuel récent** : dernières sessions, PRs, plateaus
4. **Contexte long-terme** : top-K snippets pertinents depuis la mémoire RAG
5. **Instruction utilisateur** : la question/commande
6. **Output structure** : format imposé (JSON, fields obligatoires)

### Guardrails

Contraintes obligatoires que l'agent ne peut JAMAIS violer (kcal < 1500, "skip meal", 2 jambes consécutives, etc.). Implémentation :
- Validations pré-LLM (sanity check inputs)
- Validations post-LLM (parse réponse, retry si fail)
- Liste explicite dans le system prompt
- Logging strict pour audit

### EAV (Entity-Attribute-Value)

Pattern de modélisation pour stocker des métriques hétérogènes évolutives dans une seule table (`health_metrics`). Trade-off : flexibilité maximale, requêtes plus verboses. Compensé par indexes ciblés + materialized views.

### OLAP vs OLTP

- **OLTP** (Online Transaction Processing) : requêtes sur données brutes en temps réel
- **OLAP** (Online Analytical Processing) : requêtes sur tables d'agrégation précalculées

Pour les stats fitness, on utilisera des tables agrégées (`weekly_stats`, `monthly_stats`) refresh par jobs background.

### MoSCoW

Méthode de priorisation des features :
- **M**ust have : sans ça le projet n'a aucune valeur
- **S**hould have : important mais le projet marche sans
- **C**ould have : nice-to-have
- **W**on't have (this time) : hors scope volontaire

### INVEST (qualité d'une user story)

- **I**ndependent : indépendante des autres
- **N**egotiable : pas figée dans le marbre
- **V**aluable : apporte de la valeur
- **E**stimable : on peut estimer l'effort
- **S**mall : tient dans un sprint
- **T**estable : critères clairs

### Gherkin / BDD

Format `Given / When / Then` pour les critères d'acceptation. Lisible par tout le monde. Peut être exécuté automatiquement par pytest-bdd → les specs deviennent les tests.

### Build vs Buy

À chaque feature :
- Est-ce différenciateur ? → BUILD
- Solution mature existe ? → BUY
- Mon temps est-il mieux investi ailleurs ? → BUY
- Coût maintenance long terme ? → choisir

---

## 6. USER STORIES — BRAIN CORE (A)

### US-001 — Authentification au dashboard 🔴 **MUST**

> En tant que Frederick, je veux pouvoir me connecter au dashboard avec un mot de passe fort, afin de protéger l'accès à toutes mes données personnelles centralisées dans le système.

```gherkin
Scénario 1 : Login réussi
  GIVEN je suis sur la page de connexion du dashboard
  WHEN je saisis un mot de passe correct
  THEN je suis redirigé vers le dashboard principal
  AND une session JWT est créée avec une durée de 7 jours
  AND un cookie httpOnly sécurisé est posé dans le navigateur

Scénario 2 : Login échoué
  GIVEN je suis sur la page de connexion
  WHEN je saisis un mot de passe incorrect
  THEN je vois un message d'erreur générique ("identifiants invalides")
  AND la tentative est loggée avec IP + timestamp
  AND après 5 échecs en 15 min, le login est bloqué 30 min pour cette IP

Scénario 3 : Session expirée
  GIVEN ma session JWT est expirée
  WHEN je tente d'accéder à une page protégée
  THEN je suis redirigé vers la page de login
  AND je vois un message "ta session a expiré, reconnecte-toi"

Scénario 4 : Logout
  GIVEN je suis connecté au dashboard
  WHEN je clique sur "logout"
  THEN ma session est invalidée côté serveur
  AND le cookie est supprimé côté client
  AND je suis redirigé vers la page de login
```

**Notes techniques :** mot de passe hashé avec bcrypt (coût ≥ 12), stocké dans `.env` ou secret manager.

---

### US-002 — Statut de l'agent en temps réel 🔴 **MUST**

> En tant qu'utilisateur, je veux voir en haut du dashboard l'état actuel de l'agent (idle / thinking / executing / error / sleeping), afin de comprendre ce que fait le système à tout moment.

```gherkin
Scénario 1 : Affichage du statut actuel
  GIVEN je suis connecté au dashboard
  WHEN la page principale se charge
  THEN je vois un indicateur d'état avec une des valeurs :
       - IDLE (gris) : l'agent attend
       - THINKING (bleu pulsant) : l'agent réfléchit
       - EXECUTING (vert clignotant) : l'agent exécute une tâche
       - ERROR (rouge) : l'agent est en erreur
       - SLEEPING (violet) : mode économie / nuit
  AND la donnée affichée date de moins de 5 secondes

Scénario 2 : Mise à jour temps réel
  GIVEN je regarde le dashboard
  WHEN l'état de l'agent change côté serveur
  THEN l'indicateur se met à jour automatiquement sans refresh
  AND la transition entre états est animée (fade 300ms)

Scénario 3 : Métriques live associées
  GIVEN je suis sur le dashboard
  WHEN je regarde la zone statut
  THEN je vois en plus de l'état :
       - le cycle courant
       - le nombre de tâches dans la queue
       - l'uptime depuis le dernier redémarrage
       - le timestamp de la dernière action

Scénario 4 : Perte de connexion WebSocket
  GIVEN le WebSocket se déconnecte
  WHEN la déconnexion dure plus de 10 secondes
  THEN un badge "⚠️ disconnected" apparaît
  AND le système tente une reconnexion automatique toutes les 5s
  AND une fois reconnecté, le badge disparaît et la donnée se refresh
```

**Notes techniques :** WebSocket via FastAPI + Next.js. Fallback en polling HTTP.

---

### US-003 — Direct Line (chat temps réel avec l'agent) 🔴 **MUST**

> En tant qu'utilisateur, je veux pouvoir parler à l'agent en langage naturel via un chat, afin de lui donner des commandes, poser des questions, ou simplement discuter de ma journée.

```gherkin
Scénario 1 : Envoi de message simple
  GIVEN je suis sur l'interface Direct Line
  WHEN je tape un message et j'appuie sur Entrée
  THEN mon message apparaît immédiatement dans le fil
  AND il est envoyé à l'agent via WebSocket
  AND l'indicateur "agent is thinking..." s'affiche
  AND la réponse arrive en streaming token par token

Scénario 2 : Streaming de la réponse
  GIVEN l'agent génère une réponse
  WHEN la réponse arrive du LLM
  THEN les tokens s'affichent progressivement (effet typing)
  AND je peux interrompre avec un bouton "stop"
  AND si j'interromps, la réponse partielle est conservée

Scénario 3 : Contexte conversationnel
  GIVEN j'ai déjà échangé plusieurs messages
  WHEN je pose une question référençant un échange précédent
  THEN l'agent comprend la référence sans répétition
  AND maintient la cohérence

Scénario 4 : Persistance des conversations
  GIVEN j'ai eu une conversation hier
  WHEN je reviens sur la Direct Line aujourd'hui
  THEN je vois l'historique complet
  AND je peux scroller pour relire
  AND je peux créer une "nouvelle conversation"

Scénario 5 : Quick actions contextuelles
  GIVEN l'agent vient de me répondre quelque chose
  WHEN sa réponse contient des suggestions d'action
  THEN des boutons d'action rapide s'affichent
  AND un clic envoie automatiquement la commande
```

---

### US-004 — Mémoire long-terme persistante 🔴 **MUST**

> En tant qu'utilisateur, je veux que l'agent se souvienne de tout ce que je lui ai dit dans les conversations précédentes, afin de ne pas avoir à me répéter et d'avoir une vraie continuité.

```gherkin
Scénario 1 : Mémorisation explicite
  GIVEN je discute avec l'agent
  WHEN je lui dis "souviens-toi que je préfère m'entraîner le matin"
  THEN l'agent extrait l'info et la stocke
  AND il confirme : "noté, je m'en souviendrai"
  AND cette info est associée à un tag (ex: "fitness:preference")

Scénario 2 : Rappel automatique pertinent
  GIVEN j'ai une info "je préfère m'entraîner le matin"
  WHEN je pose une question liée
  THEN l'agent retrouve via RAG
  AND il l'utilise sans que je l'aie redit

Scénario 3 : Mémorisation implicite (background)
  GIVEN je raconte un événement
  WHEN l'agent traite le message
  THEN les infos importantes sont extraites en background
  AND stockées avec leur source (timestamp)
  AND sans interrompre le flow

Scénario 4 : Listing & gestion de la mémoire
  GIVEN je suis sur la page System
  WHEN je clique sur "voir la mémoire"
  THEN je vois la liste paginée
  AND je peux filtrer par tag, date, type
  AND je peux supprimer ou marquer "obsolète"
  AND la suppression est définitive (avec confirmation)

Scénario 5 : Limite de pertinence
  GIVEN ma mémoire contient des milliers d'entrées
  WHEN l'agent fait un retrieval
  THEN il ne récupère que les K entrées les plus pertinentes (top-K, K=10)
  AND chaque entrée a un score de similarité
  AND seules celles > seuil (0.7) sont injectées dans le prompt
```

**Notes techniques :** PostgreSQL + pgvector. Embeddings : text-embedding-3-small (OpenAI) ou all-MiniLM-L6-v2 (HF local).

---

### US-005 — Historique des actions de l'agent 🟡 **SHOULD**

> En tant qu'utilisateur, je veux voir un historique chronologique de toutes les actions que l'agent a effectuées, afin de comprendre et de superviser son comportement autonome.

```gherkin
Scénario 1 : Affichage du timeline
  GIVEN je suis sur la page "Activity Log"
  WHEN la page se charge
  THEN je vois une timeline chronologique inversée
  AND chaque entrée : timestamp, agent, action, statut
  AND je peux cliquer pour le détail complet

Scénario 2 : Filtres
  GIVEN je suis sur Activity Log
  WHEN j'utilise les filtres
  THEN je peux filtrer par : agent, type, statut, dates
  AND combinables
  AND l'URL contient les filtres

Scénario 3 : Détail d'une action
  GIVEN je clique sur une action
  WHEN le détail s'ouvre
  THEN je vois : input, output, tokens, durée, coût, prompt envoyé
  AND je peux copier pour debug

Scénario 4 : Rétention des logs
  GIVEN un log a plus de 90 jours
  THEN il est automatiquement archivé (compressé)
  AND consultable mais avec délai d'accès plus long
```

---

### US-006 — Briefing quotidien automatique (split en 006a/006b) 🟡 **SHOULD**

> En tant qu'utilisateur, je veux recevoir chaque matin un briefing résumé de ma journée par notification push ET par email, afin de savoir où concentrer mon attention sans avoir à ouvrir le dashboard.

### US-006a — Briefing par email

```gherkin
Scénario 1 : Envoi quotidien programmé
  GIVEN il est l'heure configurée (par défaut 7h00)
  WHEN le scheduler déclenche le job briefing
  THEN l'agent compile un résumé :
       - missions du jour
       - alertes système
       - état des données 24h
       - suggestion principale (fitness en MVP)
  AND email HTML envoyé via Resend
  AND lien direct vers le dashboard

Scénario 2 : Pas de spam si rien à dire
  GIVEN c'est l'heure du briefing
  WHEN rien de notable
  THEN briefing court avec "nothing major today, focus on X"
  AND on n'envoie JAMAIS un email vide

Scénario 3 : Gestion d'erreur d'envoi
  GIVEN Resend retourne une erreur
  WHEN l'envoi échoue
  THEN erreur loggée
  AND retry 3 fois avec backoff
  AND si tous fail → alerte ntfy
```

### US-006b — Briefing push notification

```gherkin
Scénario 1 : Push à l'heure configurée
  GIVEN il est l'heure du briefing
  WHEN le job push se déclenche (juste après l'email)
  THEN notif ntfy au topic personnel
  AND titre + corps court (max 200 chars)
  AND priorité default
  AND lien click-through

Scénario 2 : Alertes critiques séparées
  GIVEN un événement critique survient
  WHEN détecté
  THEN notif push immédiate
  AND priorité HIGH (override silent mode)
  AND indépendant du briefing matinal
```

---

### US-007 — Configuration paramètres LLM (zone System) 🟡 **SHOULD**

> En tant qu'admin du système, je veux pouvoir configurer dans une section System protégée par un second mot de passe : le modèle LLM utilisé, le budget journalier, et router les tâches.

```gherkin
Scénario 1 : Accès à la zone System
  GIVEN je suis connecté au dashboard
  WHEN je clique sur "System"
  THEN je suis invité à un SECOND mot de passe
  AND si correct, j'accède aux paramètres avancés
  AND si 3x mal, accès bloqué 1h

Scénario 2 : Modification du modèle LLM
  GIVEN je suis dans la zone System
  WHEN je change le modèle NaviChat de Sonnet vers Haiku
  THEN sauvegardé en base
  AND tous les futurs appels utilisent le nouveau
  AND log du changement

Scénario 3 : Budget journalier d'appels
  GIVEN je définis 50 appels/jour
  WHEN les agents tentent un 51e
  THEN l'appel est rejeté
  AND alerte ntfy
  AND soit augmenter le budget, soit attendre minuit (reset auto)

Scénario 4 : Visualisation usage actuel
  GIVEN je suis dans System
  WHEN je regarde "USAGE"
  THEN je vois : appels du jour, % budget, coût estimé, par modèle
  AND drill-down par agent
```

---

### US-024 — Configuration des canaux de notification 🟢 **COULD**

```gherkin
Scénario 1 : Activation/désactivation par canal
  GIVEN je suis dans System > Notifications
  WHEN je toggle un canal (email ou push)
  THEN les futures notifs n'utilisent que les canaux actifs
  AND changement immédiat

Scénario 2 : Configuration de l'heure de briefing
  GIVEN je suis sur la config notif
  WHEN je change l'heure (ex: 7h00 → 8h30)
  THEN scheduler mis à jour
  AND prochain briefing à la nouvelle heure
```

---

## 7. USER STORIES — HEVY INGESTION (B)

### US-008 — Synchronisation automatique des workouts (polling) 🔴 **MUST**

> En tant qu'utilisateur, je veux que l'agent récupère mes workouts depuis l'API Hevy toutes les 30 minutes en mode polling (via hevy-mcp), afin d'avoir mes données à jour sans avoir à les saisir.

```gherkin
Scénario 1 : Sync incrémentale nominale
  GIVEN l'agent est démarré, hevy-mcp avec clé API valide
  AND la dernière sync réussie a eu lieu à T-30min
  WHEN le scheduler déclenche sync_hevy_workouts
  THEN l'agent appelle GET /v1/workouts/events?since=<dernière_sync>
  AND chaque workout est upserté dans 'workouts' (créé si nouveau, MAJ si modifié)
  AND chaque exercise/set upserté dans tables liées
  AND timestamp 'last_successful_sync' MAJ à la fin
  AND log structuré : {timestamp, workouts_new, workouts_updated, duration_ms, success: true}

Scénario 2 : Première sync (bootstrap)
  GIVEN c'est la toute première sync (last_successful_sync = null)
  WHEN le job sync se déclenche
  THEN fetch TOUS les workouts via GET /v1/workouts paginé
  AND tous stockés en base
  AND bootstrap marqué terminé
  AND log spécial 'bootstrap_complete'

Scénario 3 : Déduplication
  GIVEN un workout 'workout_abc123' existe déjà
  WHEN une nouvelle sync retourne ce même workout
  THEN MAJ (pas dupliqué)
  AND clé d'unicité = 'hevy_id' UNIQUE

Scénario 4 : API Hevy indisponible (5xx, timeout)
  GIVEN l'API Hevy retourne 5xx ou timeout > 10s
  WHEN le job sync tente
  THEN erreur loggée WARNING
  AND retry 3 fois avec backoff exponentiel (1min, 5min, 15min)
  AND last_successful_sync PAS MAJ
  AND si tous fail → alerte ntfy
  AND prochaine sync programmée non annulée

Scénario 5 : Rate limit (429)
  GIVEN l'API Hevy retourne 429
  WHEN l'agent reçoit
  THEN attend Retry-After (ou 60s défaut)
  AND retry une fois
  AND si 429 persiste → log warning + alerte ntfy

Scénario 6 : Clé API invalide ou révoquée
  GIVEN l'API Hevy retourne 401
  WHEN l'agent fait un appel
  THEN alerte ntfy CRITIQUE immédiate ("Hevy API key invalid")
  AND scheduler de sync_hevy mis en pause
  AND message d'erreur visible dans le dashboard
```

**Notes techniques :**
- sync toutes les 30 min via Celery beat
- last_successful_sync en base (table sync_state)
- hevy_etag ou hevy_last_event_id selon API

---

### US-008b — Migration vers webhooks Hevy 🟢 **COULD (Phase 4+)**

> Plus tard, je veux que l'agent passe en mode webhooks, afin d'avoir des updates instantanées au lieu d'attendre 30 min.

**Prérequis :** Tailscale Funnel ou Cloudflare Tunnel pour exposer l'endpoint webhook.

---

### US-008c — Sync bidirectionnelle Hevy 🟢 **COULD (Phase 4+)**

> En tant qu'utilisateur, je veux que l'agent puisse CRÉER ou MODIFIER des workouts/routines dans Hevy, afin que mes recommandations LLM se matérialisent automatiquement dans l'app sans copy-paste.

---

### US-009 — Synchronisation à la demande 🟡 **SHOULD**

```gherkin
Scénario 1 : Trigger manuel depuis le dashboard
  GIVEN je suis sur la page Fitness
  AND je viens de terminer un workout
  WHEN je clique "Sync now"
  THEN requête envoyée à l'API backend
  AND backend trigger un job sync (priorité haute)
  AND bouton affiche un spinner "Syncing..."
  AND statut en temps réel via WebSocket
  AND toast "Sync done — X new workouts"

Scénario 2 : Rate limit du bouton
  GIVEN je viens de cliquer "Sync now" il y a < 30s
  WHEN je re-clique
  THEN bouton désactivé avec tooltip "Wait Xs"
  AND aucune sync déclenchée

Scénario 3 : Sync à la demande échouée
  GIVEN je clique "Sync now"
  AND l'API Hevy retourne erreur
  WHEN la sync échoue
  THEN toast d'erreur avec détail
  AND retry possible
  AND erreur loggée dans Activity Log
```

---

### US-010 — Historique complet consolidé 🔴 **MUST**

> En tant qu'utilisateur, je veux pouvoir consulter mon historique complet de workouts avec des filtres par date / muscle / exercice, afin de tracker ma progression dans le détail.

```gherkin
Scénario 1 : Affichage de la liste paginée
  GIVEN je navigue sur "Training Log"
  WHEN la page charge
  THEN je vois la liste triée du plus récent au plus ancien
  AND chaque ligne : date, titre, durée, nb exos, volume total
  AND pagination 20 workouts (infinite scroll ou classique)
  AND requête backend < 200ms en p95

Scénario 2 : Filtre par date
  GIVEN je suis sur Training Log
  WHEN je sélectionne une plage de dates
  THEN seuls les workouts dans cette plage affichés
  AND URL contient la plage (deep-linkable)
  AND reset filtres en un clic

Scénario 3 : Filtre par groupe musculaire
  GIVEN je suis sur Training Log
  WHEN je sélectionne "Chest"
  THEN seuls workouts contenant exo chest affichés
  AND les exos non-chest dans ces workouts restent visibles

Scénario 4 : Filtre par exercice spécifique
  GIVEN je suis sur Training Log
  WHEN je tape "Bench Press"
  THEN seuls workouts contenant cet exo
  AND recherche tolérante (variantes)

Scénario 5 : Détail d'un workout
  GIVEN je clique sur un workout
  WHEN la vue détail s'ouvre
  THEN je vois : titre, date, durée, notes, tous exos avec sets
  AND PRs éventuels marqués
  AND comparaison avec workout précédent du même exo
```

---

### US-011 — État de récupération musculaire 🟡 **SHOULD**

> En tant qu'utilisateur, je veux voir un body scanner visuel qui me montre l'état de récupération de chaque groupe musculaire, afin de planifier mes prochaines séances intelligemment.

```gherkin
Scénario 1 : Affichage du body scanner
  GIVEN je suis sur Fitness
  WHEN "Body Scanner" charge
  THEN silhouette SVG segmentée par groupe musculaire
  AND chaque groupe coloré :
       - VERT (Ready to train) : > 48h
       - JAUNE (Recovering) : 24-48h
       - ROUGE (Heavy fatigue) : < 24h sollicitation lourde
       - GRIS (Neglected) : > 7 jours

Scénario 2 : Calcul de l'état de récupération
  GIVEN un groupe musculaire X
  WHEN on calcule son état
  THEN l'algo prend en compte :
       - timestamp dernier workout sollicitant X
       - volume total (sets × reps × charge moyenne)
       - fréquence sur 7 derniers jours
  AND retourne état + "recovery left in days"
  AND cache 5 min

Scénario 3 : Détail au clic
  GIVEN body scanner affiché
  WHEN clic sur groupe (ex: chest)
  THEN panel s'ouvre :
       - liste exos derniers entraînés
       - volume cumulé 7j / 30j
       - "ready to train in X days"
       - exos suggérés pour prochain entraînement

Scénario 4 : Mapping exercice → groupes musculaires
  GIVEN un exercice Hevy
  WHEN ajouté à un workout
  THEN mappé : primary + secondary
  AND mapping stocké dans 'exercise_muscle_map'
  AND rempli au bootstrap via API Hevy
```

**Notes techniques :**
- Hevy expose `primary_muscle_group` et `secondary_muscle_groups` dans `exercise_template`
- Algo simple : règle 48h secondaire / 72h primaire, ML plus tard

---

## 8. USER STORIES — ANALYSE & INSIGHTS (C)

### US-012 — Détection automatique des PRs 🔴 **MUST**

> En tant qu'utilisateur, je veux que l'agent détecte automatiquement quand je bats un record personnel, afin d'être félicité et tenir un historique de mes accomplissements.

**Types de PR détectés :**
1. PR de CHARGE (one-rep max estimé via formule Epley : `1RM = weight × (1 + reps/30)`)
2. PR de REPS À UNE CHARGE DONNÉE
3. PR de VOLUME PAR SESSION sur un exo (somme weight × reps non-warmup)
4. PR de VOLUME PAR GROUPE MUSCULAIRE par session

```gherkin
Scénario 1 : Détection PR de charge (1RM estimé)
  GIVEN je viens de logger [90kg × 5 reps] sur Bench Press
  AND mon précédent 1RM estimé sur Bench = 100kg
  WHEN l'agent traite après sync
  THEN il calcule Epley : 90 × (1 + 5/30) = 105kg
  AND 105 > 100 → PR détecté
  AND entrée créée :
       - exercise_template_id, type='one_rep_max'
       - new_value=105, old_value=100, gain=+5kg
       - workout_id, set_id, achieved_at
  AND notif ntfy "🎉 PR detected on Bench Press: 1RM 100→105kg"
  AND apparition dans Activity Log

Scénario 2 : Détection PR de reps à charge fixe
  GIVEN [80kg × 7 reps] précédent record
  WHEN je log [80kg × 8 reps]
  THEN PR 'reps_at_load' détecté pour bucket 80kg
  AND notif : "+1 rep à 80kg sur Bench Press"

Scénario 3 : Détection PR de volume session
  GIVEN volume max Bench session = 3500kg
  WHEN session où volume Bench = 3800kg
  THEN PR 'session_volume' détecté
  AND notif : "session record volume on Bench: 3800kg"

Scénario 4 : Filtres anti-faux-positifs
  GIVEN un set "warmup" ou "failure"
  WHEN on cherche des PRs
  THEN ces sets EXCLUS
  AND seuls 'normal' comptent

  GIVEN un set avec charge < 50% du max théorique
  WHEN analysé
  THEN considéré comme warmup implicite
  AND exclu

Scénario 5 : Affichage dans le détail workout
  GIVEN un workout avec PRs
  WHEN je consulte le workout
  THEN badge "🏆 PR" à côté de chaque set concerné
  AND détail au survol

Scénario 6 : Page dédiée historique des PRs
  GIVEN je suis sur Fitness > PR History
  WHEN la page charge
  THEN liste de TOUS PRs détectés, par exercice, chronologique
  AND filtre par type (1RM / reps / volume)
  AND cliquer = voir workout source
```

**Notes techniques :**
- table `personal_records`
- backfill au bootstrap pour détecter PRs passés
- formule Epley par défaut (1RM = weight × (1 + reps/30))

---

### US-013 — Détection plateaus, régressions et "behind schedule" (context-aware) 🟡 **SHOULD**

> En tant qu'utilisateur, je veux que l'agent identifie quand un exercice plafonne ou régresse, afin d'ajuster ma stratégie avant de stagner trop longtemps.

```gherkin
Scénario 1 : Calcul de la trajectoire de progression attendue
  GIVEN un exercice X a un exercise_target actif
  AND on est à T = set_at + N semaines
  WHEN l'agent calcule la trajectoire attendue
  THEN interpolation linéaire entre baseline et target :
       - expected_weight_at_T = baseline + (target - baseline) × (N / estimated_weeks_max)
       - borne MAX du timeline pour tolérance
  AND coefficient selon context_phase :
       - cutting → 0.7 (70% progression linéaire attendue)
       - maintenance → 1.0
       - bulking → 1.3

Scénario 2 : Détection "behind schedule" (alerte précoce)
  GIVEN exercise_target 13 semaines, baseline 52.5kg, target 70kg
  AND semaine 7 (>50% timeline)
  AND trajectoire attendue ajustée cutting = 58.5kg
  WHEN les 3 dernières sessions montrent moyenne max = 54kg
  THEN flag 'behind_schedule' avec gap = -4.5kg
  AND notif soft : "you're behind schedule on Bench Press (54kg vs 58.5kg expected)"
  AND analyse LLM des causes possibles

Scénario 3 : Détection plateau "officiel"
  GIVEN exercise_target expected_completion_date dépassée
  AND performance < target_weight_kg_min
  WHEN analyse nightly tourne
  THEN plateau 'official_plateau' flaggé
  AND notif + recommandation LLM :
       - revoir le target
       - changer variation
       - deload structuré
       - check nutrition/sommeil

Scénario 4 : Détection plateau "stalled"
  GIVEN aucune progression sur 4 sessions consécutives
  AND charge max strictement identique
  WHEN analyse tourne
  THEN plateau 'stalled' flaggé (indépendamment des targets)
  AND résolu dès qu'un PR survient

Scénario 5 : Détection régression
  GIVEN sur exo X, moyenne 1RM Epley sur 3 dernières sessions < 95% session 4 précédente
  WHEN analyse tourne
  THEN régression flaggée
  AND severity : 'minor' (<5%), 'moderate' (5-10%), 'major' (>10%)
  AND notif adaptée
  AND vérif si cutting démarré récemment → si oui suggère que c'est normal

Scénario 6 : Reset du flag plateau
  GIVEN plateau actif sur exo X
  WHEN PR ou progression vers target détecté
  THEN plateau marqué 'resolved'
  AND notif positive : "plateau broken on Bench Press 💥"

Scénario 7 : Achievement d'un target
  GIVEN exercise_target status='active'
  WHEN log un set qui atteint ou dépasse target_weight_kg_min × target_reps_min
  THEN target → status='achieved'
  AND achieved_at posé
  AND notif spéciale : "🎯 target reached on Bench Press: 65kg × 8!"
  AND propose nouveau target (Phase 4+)

Scénario 8 : Visualisation graphique
  GIVEN je consulte la page détail d'un exercice
  WHEN la vue charge
  THEN graphique 12 semaines avec :
       - progression réelle (bleue)
       - trajectoire attendue (verte pointillée)
       - trajectoire ajustée context (grise pointillée)
       - target (zone hachurée)
       - PRs (étoiles)
       - zones plateau/régression (rouge/orange)
```

**Notes techniques :**
- projections linéaires au MVP, modèles ML plus tard
- coefficient tolérance configurable
- alertes remontées dans briefing matinal

---

### US-013b — Tracking de progression vers les targets 🟡 **SHOULD**

```gherkin
Scénario 1 : Dashboard Targets sur Fitness
  GIVEN je suis sur la page Fitness
  WHEN "Targets Progress" charge
  THEN liste des exercise_targets actifs
  AND chaque target :
       - nom de l'exo
       - baseline → current → target
       - progress bar avec % atteint
       - "X weeks left of estimated timeline"
       - badge statut (on_track / behind_schedule / ahead / achieved / expired)
  AND tri par % achievement, weeks left, ou status

Scénario 2 : Calcul du % d'achievement
  GIVEN target {baseline: 52.5, target: 65-70}
  AND performance actuelle = 58kg
  WHEN calcul %
  THEN progress_pct = (58 - 52.5) / (65 - 52.5) = 44%

Scénario 3 : Notification milestone
  GIVEN target passe par 25% / 50% / 75% / 100%
  WHEN milestone franchi
  THEN notif :
       - 25% : "quarter way there 💪"
       - 50% : "halfway 🔥"
       - 75% : "75% there, final push 🚀"
       - 100% : (US-013 scénario 7)

Scénario 4 : Vue détaillée d'un target
  GIVEN je clique sur un target
  WHEN la vue détail s'ouvre
  THEN :
       - graphique progression vs trajectoire (US-013 scénario 8)
       - historique sets depuis baseline
       - recos LLM contextuelles (Phase 4+)
       - actions : "revise target" / "abandon" / "set new"
```

---

### US-013c — Gestion de la transition d'équipement 🟢 **COULD**

```gherkin
Scénario 1 : Déclaration manuelle d'une transition
  GIVEN je change de salle/d'équipement
  WHEN je marque "I switched gym/equipment on date X"
  THEN entrée 'equipment_transition' créée
  AND alertes "MAJOR REGRESSION" désactivées 2 semaines
  AND exos concernés re-baseline à la prochaine session

Scénario 2 : Mapping exercice libre → machine
  GIVEN je passe du Bench Press barre à HS Chest Press
  WHEN l'agent traite la prochaine session
  THEN détecte (via historique) que Bench plus fait
  AND propose : "you've started HS Chest Press — link to Bench Press target?"
  AND si j'accepte → exercise_target cloné/lié avec nouveau baseline
```

---

### US-014 — Identification des groupes musculaires négligés 🟡 **SHOULD**

```gherkin
Scénario 1 : Calcul des "jours depuis dernière sollicitation"
  GIVEN je consulte le dashboard Fitness
  WHEN "Muscle Status" charge
  THEN pour CHAQUE groupe :
       - days_since_last_trained
       - volume_last_7d
       - frequency_last_30d
  AND cache 5 min

Scénario 2 : Flag de négligence
  GIVEN un groupe X
  WHEN days_since_last_trained > 7 jours
  THEN flaggé "neglected"
  AND gris dans body scanner
  AND apparaît dans "Insights"
  AND notif soft 1x/sem : "you haven't trained lower_back in 9 days"

Scénario 3 : Flag de sur-sollicitation
  GIVEN un groupe X
  WHEN frequency_last_7d >= 4 ET volume_last_7d > 1.5 × moyenne_4sem_précédentes
  THEN flaggé "high_load"
  AND notif : "high training load on X this week — watch recovery"

Scénario 4 : Vue tableau Insights
  GIVEN je consulte "Insights"
  WHEN charge
  THEN tableau résumé :
       | muscle group | last trained | volume 7d | freq 30d | status |
  AND tri par colonne

Scénario 5 : Suggestion d'exercices
  GIVEN un groupe flaggé neglected
  WHEN je clique
  THEN propose 3-5 exos pour ce groupe
  AND tirés de mes exos déjà connus
  AND "ajouter à mon prochain workout" (Phase 4+)
```

---

### US-015 — Stats hebdomadaires & mensuelles 🟡 **SHOULD**

```gherkin
Scénario 1 : Vue stats semaine en cours
  GIVEN je suis sur Fitness > Stats
  WHEN je sélectionne "This week"
  THEN dashboard avec :
       - nb sessions / objectif hebdo
       - durée totale
       - volume total
       - répartition volume par groupe (pie / bar)
       - nb PRs détectés
       - sessions par jour (heatmap)

Scénario 2 : Comparaison semaine vs précédente
  GIVEN je suis sur Stats > Weekly
  WHEN je regarde chaque metric
  THEN delta vs semaine précédente :
       - "12,500 kg total (+8% vs last week)" vert si positif
       - "3 sessions (-1 vs last week)" orange si négatif
  AND comparaison arbitraire deux semaines

Scénario 3 : Vue stats mois en cours
  GIVEN "This month"
  WHEN charge
  THEN mêmes metrics agrégées au mois
  AND graphique temporel évolution semaine par semaine
  AND moyenne mobile 4 semaines

Scénario 4 : Volume par exercice (top 10)
  GIVEN page stats
  WHEN "Top exercises"
  THEN 10 exos avec plus de volume cumulé
  AND chaque : nom, volume total, sessions, 1RM actuel

Scénario 5 : Export des stats
  GIVEN page stats
  WHEN je clique "Export CSV"
  THEN fichier CSV avec données brutes
  AND téléchargement
  AND événement loggé

Scénario 6 : Précalcul des stats
  GIVEN agrégations potentiellement lourdes
  WHEN un workout sync'd
  THEN job background MAJ :
       - weekly_stats
       - monthly_stats
       - exercise_aggregates
  AND pages hit ces tables agrégées (pas calcul à la volée)
  AND graphiques chargent < 100ms
```

**Notes techniques :** materialized views Postgres pour les agrégations.

---

## 9. USER STORIES — COACHING (D)

### US-016 — Suggestion du prochain workout 🔴 **MUST**

> En tant qu'utilisateur, je veux que l'agent me suggère quel workout faire aujourd'hui, en fonction de mon split + état de récupération + dernière séance.

```gherkin
Scénario 1 : Reco du workout du jour basée sur le split
  GIVEN je suis sur le dashboard Fitness et il est 7h00
  AND nous sommes mardi
  AND split actif "PPL+Upper+Street"
  AND mardi mappé à "pull"
  WHEN l'agent calcule la suggestion
  THEN vérif données contextuelles :
       - dernier workout
       - état récupération par groupe (US-011)
       - sommeil dernière nuit (US-026)
       - HRV récente (delta vs moyenne 7j)
       - plateaus actifs (US-013)
       - phase nutrition (cutting)
  AND construit prompt structuré
  AND appelle LLM avec output JSON forcé :
       {
         "recommendation": "...",
         "reasoning": "...",
         "exercises": [{name, sets, reps, weight_suggestion, notes}],
         "expected_duration_min": 60,
         "warnings": [],
         "alternative_if_tired": "..."
       }
  AND stockée dans workout_suggestions
  AND affichée avec boutons "accept" / "modify" / "reject"

Scénario 2 : Adaptation au sommeil insuffisant
  GIVEN dernière nuit < 6h
  WHEN l'agent calcule
  THEN warning : "tu as peu dormi, on allège"
  AND charges réduites ~10%
  AND skip isolation à RPE > 9
  AND session plus courte (45 vs 75 min)

Scénario 3 : Adaptation à un groupe en haute fatigue
  GIVEN aujourd'hui push mais triceps "high load"
  WHEN l'agent calcule
  THEN switch triceps lourds vers léger
  AND note explicative dans reasoning
  AND ne descend pas sous "minimum effective dose"

Scénario 4 : Conflit avec le programme prévu
  GIVEN aujourd'hui pull selon split
  AND "j'ai 30 min seulement"
  WHEN l'agent recalcule
  THEN session pull tronquée :
       - 2-3 exos compound prioritaires
       - sets réduits
       - "session courte — on rattrape samedi"
  AND sauvegarde "training debt"

Scénario 5 : Override manuel
  GIVEN suggestion générée
  WHEN je clique "modify"
  THEN UI pour remplacer/ajouter/retirer exos
  AND chaque modif trackée (event 'user_override')
  AND patterns d'override nourrissent l'apprentissage (Phase 4+)

Scénario 6 : Reject avec feedback
  GIVEN suggestion générée
  WHEN je clique "reject" + raison
  THEN raison stockée
  AND regénère avec contrainte
  AND si "blessure léger genou" → flag temporaire qui exclut exos genou 3-7 jours

Scénario 7 : Guardrails appliqués
  GIVEN suggestion contient :
       - 2 jours legs consécutifs
       - > 8 exos
       - hausse > 10% sur tous compound
       - skipping repas/eau
  THEN REJETÉE par guardrails post-LLM
  AND retry avec prompt amendé
  AND si 3 retries fail → fallback "safe template"
  AND incident loggé
```

**Notes techniques :**
- stockage : suggestion + prompt complet + réponse brute → traçabilité totale
- track coût en tokens
- "safe templates" pré-définis (1 par jour split)

---

### US-017 — Plan nutritionnel adaptatif quotidien 🔴 **MUST**

```gherkin
Scénario 1 : Plan nutrition jour d'entraînement
  GIVEN workout prévu/loggé
  AND phase 'cutting' avec target 1650 kcal, 180-200g prot
  WHEN je consulte "Nutrition" à 7h
  THEN plan structuré :
       {
         "daily_kcal_target": 1650,
         "daily_protein_target_g": 195,
         "daily_carbs_target_g": 180,
         "daily_fats_target_g": 55,
         "hydration_target_l": 4.5,
         "timing_strategy": "carb_periodized",
         "meal_distribution": [
           { meal: "breakfast", kcal: 400, protein: 40, notes: "slow carbs" },
           { meal: "pre_workout", kcal: 250, protein: 20, notes: "30g carbs 1h before" },
           { meal: "post_workout", kcal: 450, protein: 50, notes: "fast protein + carbs" },
           { meal: "dinner", kcal: 550, protein: 60, notes: "high protein moderate carbs" }
         ],
         "supplements_today": [
           { name: "Creatine", timing: "anytime" },
           { name: "Whey", timing: "post_workout" }
         ]
       }
  AND chaque meal cliquable pour suggestions (US-018)

Scénario 2 : Plan nutrition jour de repos
  GIVEN jour de repos
  WHEN l'agent calcule
  THEN glucides réduits (~120g vs 180g)
  AND protéines maintenues
  AND graisses légèrement augmentées
  AND timing "spread protein every 3-4h"

Scénario 3 : Adaptation NEAT live
  GIVEN il est 18h00
  AND steps = 12 000 (target 8 000)
  AND pas encore mangé 80% kcal
  WHEN l'agent ré-évalue
  THEN ajuste à la hausse kcal restants (+150)
  AND notif : "tu as été plus actif, meal plus copieux possible"

Scénario 4 : Adaptation poids
  GIVEN je log mon poids
  AND moyenne 7j descend trop vite (>1% BW/sem)
  WHEN analyse hebdo
  THEN alerte : "weight loss too fast — risk muscle loss, +100 kcal?"
  AND propose ajustement training_context.daily_kcal_target

Scénario 5 : Hydratation tracking
  GIVEN target 4L/jour
  WHEN il est 16h et j'ai logé 1.5L
  THEN notif push "drink some water, 2.5L below target"
  AND timing : "0.5L now, 0.5L 18h, 1L dinner"

Scénario 6 : Guardrails nutrition
  GIVEN plan calculé
  WHEN contient :
       - kcal_total < 1500 (sauf override explicite)
       - protein < 1.6g/kg BW
       - "skip meal"
       - eau < 2.5L/jour
  THEN guardrails REJET
  AND fallback baseline
  AND incident logué + alerte ntfy
```

---

### US-018 — Suggestions de meals contextuelles (avec Cronometer) 🟡 **SHOULD**

```gherkin
Scénario 1 : Lecture des meals déjà loggés
  GIVEN je log mes meals dans Cronometer pendant la journée
  WHEN sync horaire via cronometer-mcp
  THEN meals du jour récupérés avec macros détaillées
  AND MAJ "kcal/macros restants" sur dashboard
  AND delta vs daily targets calculé

Scénario 2 : Suggestion intelligente du prochain meal
  GIVEN 12h00, déjà 500 kcal (breakfast)
  AND reste 1150 kcal, 140g prot à atteindre
  AND meal_distribution lunch ~500 kcal / 50g prot
  WHEN je clique "suggest next meal"
  THEN 3 options matchant macros restantes
  AND chaque option :
       - kcal, prot/glu/lip
       - aliments présents dans historique Cronometer
       - "log this meal" → notif push pour logger dans Cronometer

Scénario 3 : Post-workout immediate
  GIVEN viens de logger workout via Hevy
  AND fenêtre 0-60 min post-séance
  WHEN l'agent détecte
  THEN notif push : "post-workout window — log this asap"
  AND suggestion : "Whey 30g + banane + Creatine 5g"
  AND track combien de temps après workout je logge

Scénario 4 : Apprentissage des patterns batch cooking
  GIVEN log régulier mêmes meals (batch)
  WHEN analyse 30j Cronometer
  THEN identifie "go-to meals" auto
  AND propose en priorité
  AND suggère "tu manges X le mardi midi" (pattern)

Scénario 5 : Détection de gap (kcal/prot non logged)
  GIVEN 22h00, logé 1200 kcal (target 1650)
  WHEN check de soir
  THEN alerte : "73% de ton target — soit non logé soit ajuster"
  AND "do you want to log a forgotten meal?" → deep link Cronometer
```

---

### US-019 — Challenges hebdomadaires 🟡 **SHOULD**

```gherkin
Scénario 1 : Generation des challenges chaque dimanche
  GIVEN dimanche 20h00 (configurable)
  WHEN scheduler trigger 'weekly_challenge_generation'
  THEN analyse semaine écoulée :
       - sessions complétées vs target
       - PRs détectés
       - groupes négligés
       - progression vs targets
       - sommeil moyen
       - kcal compliance
  AND génère 2-3 challenges semaine suivante
  AND chaque challenge :
       - title
       - description
       - mesurable goal
       - tracking method (auto/manuel)
       - reward (XP)
       - deadline

Scénario 2 : Types de challenges adaptés au contexte
  GIVEN cutting + plateau actif sur bench
  WHEN générés
  THEN typiques :
       - "break the plateau"
       - "consistency" → 4+ sessions
       - "neglected group" → 2 sessions lower back
       - "sleep king" → 5+ nuits à 7h+
       - "step goal" → 56 000 pas
       - "hydration hero" → 4L+ pendant 5 jours

Scénario 3 : Progress tracking auto
  GIVEN challenge "8000 steps/jour 5 jours" actif
  AND mercredi soir
  WHEN je consulte dashboard
  THEN affiche : "3/5 days completed ✓ ✓ ✗ ✓"
  AND push si retard : "encore 2 jours à 8K"

Scénario 4 : Complétion + reward
  GIVEN criteria remplis
  WHEN détection
  THEN marqué "completed"
  AND notif "🏆 challenge complete"
  AND XP attribués (US-022/023)
  AND propose challenge suivant en hardcore

Scénario 5 : Échec gracieux
  GIVEN non complété en fin de sem
  WHEN bilan dimanche
  THEN marqué "failed" (sans drama)
  AND analyse : "tu étais à 60% — next time"
  AND reprise possible
```

---

## 10. USER STORIES — CHAT COACH (E)

### US-020 — Chat coach contextuel (mode Fitness) 🟡 **SHOULD**

```gherkin
Scénario 1 : Activation du mode coach
  GIVEN je suis sur Fitness > Coach Chat
  WHEN la page charge
  THEN interface chat avec préfix "PASSION · COACH"
  AND system prompt enrichi :
       - persona "coach fitness expert, encourageant mais direct"
       - tout training_context
       - 5 dernières sessions (résumé compact)
       - plateaus actifs
       - derniers PRs
       - session du jour si applicable
       - insights récents
  AND latence ouverture < 500ms (contexte pré-loadé)

Scénario 2 : Question technique sur forme d'exercice
  GIVEN je tape "comment je sais si mon bench press est bien fait ?"
  WHEN l'agent répond
  THEN réponse personnalisée :
       - points clés forme bench
       - rappel notes existantes si pertinent
       - cues mentaux
  AND propose actions de suivi (filmer prochaine session)

Scénario 3 : Question programmation
  GIVEN "j'ai pas le temps demain pour mon push, je peux le pousser à vendredi ?"
  WHEN l'agent répond
  THEN analyse impact :
       - vendredi = Upper → conflit
       - déplacement intelligent (push samedi à place de street)
       - prévient risques (back-to-back chest)
  AND propose MAJ calendrier (Phase 4+)

Scénario 4 : Question nutrition contextuelle
  GIVEN "j'ai eu une grosse journée niveau stress, je peux me permettre un cheat meal ce soir ?"
  WHEN l'agent répond
  THEN prend en compte :
       - semaine kcal vs target
       - sommeil récent
       - progression targets
       - phase (cutting → moins marge)
  AND réponse nuancée, pas binaire
  AND JAMAIS la morale

Scénario 5 : Sentiment-aware coaching
  GIVEN "je suis épuisé, j'ai pas envie de m'entraîner"
  WHEN détecte le ton
  THEN ajuste son style :
       - empathie d'abord
       - analyse rapide signaux (sommeil, HRV, kcal)
       - propose : deload / rest / workout très court
       - jamais "no excuses bro"
  AND enregistre l'événement dans mémoire long-terme (US-004)

Scénario 6 : Streaming + interruption
  GIVEN réponse à question complexe
  WHEN streaming
  THEN je peux interrompre à tout moment
  AND nouveau message en streaming → ancien stop, nouveau traité
```

---

### US-021 — Quick actions contextuelles dans le chat coach 🟢 **COULD**

```gherkin
Scénario 1 : Boutons par défaut au démarrage
  GIVEN j'ouvre le chat coach fitness 1ère fois du jour
  WHEN l'interface charge
  THEN 4 boutons au-dessus de l'input :
       - "📊 show today's stats"
       - "📋 today's workout plan"
       - "🥗 what should I eat now?"
       - "💤 sleep summary"
  AND chaque bouton = commande prédéfinie

Scénario 2 : Boutons contextuels après réponse
  GIVEN réponse suggérant une action
  WHEN je regarde le chat
  THEN boutons contextuels :
       - "Schedule it" (Phase 4+)
       - "Show my PR history on bench"
       - "Skip suggestion"
  AND clic envoie commande

Scénario 3 : Customisation des quick actions
  GIVEN System > Chat preferences (Phase 4+)
  WHEN je veux changer
  THEN activer/désactiver chaque bouton
  AND ajouter mes raccourcis
```

---

## 11. USER STORIES — GAMIFICATION (F)

### US-022 — Streaks d'entraînement 🟡 **SHOULD**

```gherkin
Scénario 1 : Calcul du streak workout
  GIVEN je consulte le dashboard Fitness
  WHEN "Streak" charge
  THEN streak actuel défini comme :
       - jours consécutifs respectant le plan
       - "respecté" = workout fait OU rest planifié
       - skip sans rest planifié → casse le streak
  AND aussi : best streak ever, current record, days to beat

Scénario 2 : Streak nutrition
  GIVEN dans la zone
  WHEN je regarde
  THEN streak nutrition séparé :
       - jours consécutifs dans marge ±10% kcal target
       - basé sur logs Cronometer

Scénario 3 : Streak sleep
  GIVEN dans la zone
  WHEN je regarde
  THEN streak sleep :
       - jours consécutifs dormi 7h-9h (target)
       - basé sur Health Connect

Scénario 4 : Notification à la rupture
  GIVEN streak en cours (workout: 12 jours)
  WHEN pas de workout aujourd'hui ET pas de rest planifié
  THEN 22h00 notif "⚠️ workout streak en danger — il te reste 2h"
  AND si pas terminé → streak 0 lendemain
  AND notif douce "your streak ended at 12 days"

Scénario 5 : Pas de streak shaming
  GIVEN malade / blessé / vacances
  WHEN je clique "freeze streak"
  THEN streak gelé jusqu'à retour
  AND freeze max 7 jours/mois (anti-abuse)
  AND aucune notif punitive pendant freeze
```

---

### US-023 — Missions journalières & système XP 🟡 **SHOULD**

```gherkin
Scénario 1 : Missions du jour
  GIVEN je suis sur dashboard à 6h
  WHEN "Daily Missions" charge
  THEN 2-3 missions :
       - basées sur jour semaine
       - sur goals du moment
       - sur négligences récentes
  AND chaque mission : XP reward (50 / 100 / 200)

Scénario 2 : Types de missions
  GIVEN l'agent génère
  WHEN choisit dans le pool
  THEN types possibles :
       - "complete workout" (XP: 100)
       - "log all meals" (XP: 50)
       - "hit kcal target ±10%" (XP: 75)
       - "hit step target" (XP: 50)
       - "drink 4L water" (XP: 50)
       - "sleep 7+ hours" (XP: 75)
       - "daily check-in" (XP: 25)
       - "review training log" (XP: 25)
       - "set a PR" (XP: 200, bonus)

Scénario 3 : Auto-complétion via tracking
  GIVEN mission "log all meals" active
  WHEN logue dans Cronometer + sync done
  THEN mission auto "completed"
  AND XP + notif "✓ mission complete"

Scénario 4 : Système de niveau
  GIVEN accumule XP
  WHEN atteint seuils
  THEN monte de niveau :
       - Recruit (0 XP)
       - Trainee (500)
       - Operator (1500)
       - Specialist (3500)
       - Expert (7500)
       - Master (15000)
  AND débloquage cosmétique / titre
  AND niveau affiché dans top bar

Scénario 5 : Récap hebdomadaire
  GIVEN dimanche soir
  WHEN weekly briefing tourne
  THEN inclus :
       - XP gagnés cette semaine
       - missions completed / total
       - niveau actuel + % vers le suivant
       - top 3 achievements
```

**Notes techniques :**
- table `missions` avec status (pending/in_progress/completed/failed/expired)
- table `xp_log` pour audit
- table `user_level` avec current_xp + level

---

## 12. USER STORIES — HEALTH METRICS

### US-025 — Ingestion auto des données Health Connect via Tasker 🔴 **MUST**

> En tant qu'utilisateur, je veux que les données Health Connect (sommeil, NEAT, HR, HRV, SpO2) soient automatiquement ingérées par l'agent.

**Fréquence finale : toutes les heures (24 push/jour).**

```gherkin
Scénario 1 : Sync horaire réussie
  GIVEN Tasker configuré sur mon Android avec AutoHealth Connect
  AND ma clé d'ingestion est valide
  WHEN il est xx:00 (heure ronde)
  THEN Tasker lit toutes les data Health Connect de l'heure écoulée
  AND POST /api/v1/health/ingest
  AND endpoint reçoit, valide, upsert dans health_metrics
  AND déduplication via source_record_id
  AND ingest_summary créé : { count_records, count_new, duration_ms }
  AND matview daily_health_summary refresh

Scénario 2 : Schema validation strict
  GIVEN un payload arrive
  WHEN invalide (champ manquant, type incorrect, > 5MB)
  THEN 400 avec détail
  AND aucune donnée insérée
  AND Tasker retry nuit d'après
  AND alerte ntfy "health ingest schema error"

Scénario 3 : Auth invalide
  GIVEN payload sans header X-Ingest-Token ou invalide
  WHEN endpoint traite
  THEN 401 immédiatement
  AND alerte ntfy CRITIQUE
  AND IP trackée

Scénario 4 : Idempotence
  GIVEN payload avec records déjà ingérés
  WHEN endpoint traite
  THEN records déjà connus skip (pas d'erreur, pas dup)
  AND seuls nouveaux insérés
  AND count_new reflète delta réel

Scénario 5 : Backfill manuel
  GIVEN trou dans données (Tasker a planté un jour)
  WHEN je trigger CLI ou bouton "backfill health" avec [start, end]
  THEN Tasker pousse data sur cette fenêtre
  AND déduplication empêche doublons
```

**Notes techniques :**
- endpoint protégé par **token statique** dans `.env`, header X-Ingest-Token
- exposition : **Tailscale uniquement** (pas d'exposition publique)
- types Health Connect supportés : Sleep, Steps, Distance, Active/Total Calories, Floors, Elevation, ExerciseSession, HeartRate, RestingHR, HRV (RMSSD), BloodOxygen, RespiratoryRate, SkinTemperature, Weight, BodyFat, LeanBodyMass, BoneMass, Hydration

---

### US-026 — Daily health snapshot 🟡 **SHOULD**

```gherkin
Scénario 1 : Affichage du daily snapshot
  GIVEN je suis sur le dashboard
  WHEN "today's health" charge
  THEN pour la journée :
       - durée sommeil dernière nuit + qualité (basée sur stages)
       - HR au repos
       - HRV (avec delta vs moyenne 7j)
       - steps actuels
       - kcal NEAT cumulés
  AND chaque metric statut visuel (vert/jaune/rouge) selon targets

Scénario 2 : Trend chart 7j
  GIVEN je suis sur Fitness > Health Trends
  WHEN la vue charge
  THEN pour chaque metric un graphique 7j (line)
  AND switch entre 7j / 30j / 90j
  AND targets affichées en pointillés

Scénario 3 : Manquant data
  GIVEN un jour sans données reçues
  WHEN je consulte
  THEN gris/striped sur graphs
  AND message "missing data — last sync was X days ago"
  AND trigger backfill manuel possible
```

---

### US-027 — Saisie manuelle de health markers 🟡 **SHOULD**

> En tant qu'utilisateur, je veux pouvoir saisir manuellement des marqueurs de santé (prises de sang, mesures corporelles) que l'agent pourra utiliser dans son contexte.

```gherkin
Scénario 1 : Form de saisie blood panel
  GIVEN je suis sur Health > Manual Entry
  WHEN je clique "add blood panel"
  THEN formulaire :
       - date (default = today)
       - fasting state (oui/non)
       - source/labo (texte libre)
       - liste extensible de markers (testosterone, hba1c, ldl, hdl, vitD, etc.)
       - notes
       - upload PDF optionnel
  AND sauvegarde → entrée dans health_markers

Scénario 2 : Référence values
  GIVEN je saisis une valeur (ex: testosterone 5.2 ng/mL)
  WHEN le formulaire valide
  THEN comparaison auto avec plages de référence
  AND indique : "below normal" / "normal" / "elevated" / "out of range"
  AND statuts stockés dans normalized_metrics
```

---

## 13. USER STORIES — NOTIFICATIONS

### US-006a — Briefing par email (Resend)

Voir section [6. Brain Core](#6-user-stories--brain-core-a).

### US-006b — Briefing push notification (ntfy.sh)

Voir section [6. Brain Core](#6-user-stories--brain-core-a).

---

## 14. MODÈLES DE DONNÉES

### 14.1 Tables Hevy / Workouts

```sql
-- Workouts sync'd depuis Hevy
CREATE TABLE workouts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  hevy_id VARCHAR UNIQUE NOT NULL,
  title VARCHAR,
  description TEXT,
  start_time TIMESTAMPTZ,
  end_time TIMESTAMPTZ,
  hevy_created_at TIMESTAMPTZ,
  hevy_updated_at TIMESTAMPTZ,
  synced_at TIMESTAMPTZ DEFAULT NOW(),
  raw_data JSONB  -- payload Hevy complet
);

CREATE TABLE workout_exercises (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workout_id UUID REFERENCES workouts(id) ON DELETE CASCADE,
  exercise_template_id VARCHAR,
  title VARCHAR,
  order_index INT,
  notes TEXT,
  superset_id VARCHAR
);

CREATE TABLE workout_sets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workout_exercise_id UUID REFERENCES workout_exercises(id) ON DELETE CASCADE,
  order_index INT,
  set_type VARCHAR,  -- 'warmup' | 'normal' | 'failure' | 'dropset'
  weight_kg NUMERIC,
  reps INT,
  rpe NUMERIC,
  distance_meters NUMERIC,
  duration_seconds INT
);

CREATE TABLE exercise_templates (
  hevy_id VARCHAR PRIMARY KEY,
  title VARCHAR,
  primary_muscle_group VARCHAR,
  secondary_muscle_groups VARCHAR[],
  equipment VARCHAR,
  exercise_type VARCHAR
);

CREATE TABLE sync_state (
  id INT PRIMARY KEY DEFAULT 1,
  last_successful_sync TIMESTAMPTZ,
  bootstrap_completed BOOLEAN DEFAULT FALSE,
  last_error TEXT,
  last_error_at TIMESTAMPTZ
);
```

### 14.2 Tables Context / Targets

```sql
CREATE TABLE training_context (
  id INT PRIMARY KEY DEFAULT 1,
  
  -- phase
  phase VARCHAR,                      -- 'cutting' | 'bulking' | 'maintenance' | 'recomp'
  phase_started_at DATE,
  phase_target_end_date DATE,
  
  -- corps
  current_weight_kg NUMERIC,
  current_body_fat_pct NUMERIC,
  target_weight_kg NUMERIC,
  target_body_fat_pct NUMERIC,
  
  -- nutrition
  daily_kcal_target INT,
  daily_protein_g_target_min INT,
  daily_protein_g_target_max INT,
  daily_hydration_l_target NUMERIC,
  
  -- sommeil
  sleep_target_hours_min NUMERIC,
  sleep_target_hours_max NUMERIC,
  bedtime_target TIME,
  wakeup_target TIME,
  
  -- NEAT
  daily_steps_target INT,
  weekly_long_walks_target INT,
  
  -- training
  weekly_session_target INT,
  active_split VARCHAR,
  
  -- supplements (liste flexible)
  supplements JSONB,
  
  notes TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE exercise_targets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exercise_template_id VARCHAR REFERENCES exercise_templates(hevy_id),
  
  -- snapshot baseline
  baseline_weight_kg NUMERIC,
  baseline_reps INT,
  baseline_1rm_estimate NUMERIC,
  baseline_recorded_at TIMESTAMPTZ,
  
  -- cibles
  target_weight_kg_min NUMERIC,
  target_weight_kg_max NUMERIC,
  target_reps_min INT,
  target_reps_max INT,
  target_1rm_estimate NUMERIC,
  
  -- timeline
  estimated_weeks_min INT,
  estimated_weeks_max INT,
  set_at TIMESTAMPTZ DEFAULT NOW(),
  expected_completion_date DATE,
  
  -- typologie
  exercise_type VARCHAR,              -- 'compound_free' | 'compound_machine' 
                                      -- | 'isolation' | 'calisthenics_progressive'
                                      -- | 'cardio_endurance'
  track_1rm BOOLEAN DEFAULT TRUE,
  track_volume BOOLEAN DEFAULT TRUE,
  track_reps BOOLEAN DEFAULT TRUE,
  
  workout_day VARCHAR,                -- 'push' | 'pull' | 'legs' | 'upper' | 'street' | 'mixed'
  
  -- pour calisthéniques
  progression_chain JSONB,
  bodyweight_dependent BOOLEAN DEFAULT FALSE,
  bw_threshold_kg NUMERIC,
  
  -- contexte
  context_phase VARCHAR,
  notes TEXT,
  
  -- état
  status VARCHAR DEFAULT 'active',    -- 'active' | 'achieved' | 'expired' | 'abandoned' | 'revised'
  achieved_at TIMESTAMPTZ,
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE program_split (
  id INT PRIMARY KEY DEFAULT 1,
  split_name VARCHAR,
  
  -- planning hebdomadaire
  monday VARCHAR,
  tuesday VARCHAR,
  wednesday VARCHAR,
  thursday VARCHAR,
  friday VARCHAR,
  saturday VARCHAR,
  sunday VARCHAR,
  
  -- composition de chaque jour
  day_compositions JSONB,
  
  active_since DATE,
  active_until DATE,
  notes TEXT
);
```

### 14.3 Tables Analyse

```sql
CREATE TABLE personal_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exercise_template_id VARCHAR REFERENCES exercise_templates(hevy_id),
  pr_type VARCHAR,                    -- 'one_rep_max' | 'reps_at_load' | 'session_volume' | 'muscle_group_volume'
  new_value NUMERIC,
  old_value NUMERIC,
  gain NUMERIC,
  bucket VARCHAR,                     -- pour reps_at_load (ex: "80kg")
  workout_id UUID REFERENCES workouts(id),
  workout_set_id UUID REFERENCES workout_sets(id),
  achieved_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE exercise_analysis (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exercise_template_id VARCHAR REFERENCES exercise_templates(hevy_id),
  analysis_type VARCHAR,              -- 'plateau' | 'regression' | 'behind_schedule'
  severity VARCHAR,                   -- 'minor' | 'moderate' | 'major' (régression)
  details JSONB,
  status VARCHAR DEFAULT 'active',    -- 'active' | 'resolved'
  resolved_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Aggregations (matérialisées, refresh par job background)
CREATE TABLE weekly_stats (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  week_start DATE,
  total_sessions INT,
  total_duration_minutes INT,
  total_volume_kg NUMERIC,
  volume_per_muscle_group JSONB,
  pr_count INT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (week_start)
);

CREATE TABLE monthly_stats (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  month_start DATE,
  total_sessions INT,
  total_duration_minutes INT,
  total_volume_kg NUMERIC,
  volume_per_muscle_group JSONB,
  pr_count INT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (month_start)
);
```

### 14.4 Tables Health Metrics

```sql
-- EAV pattern : une ligne par data point
CREATE TABLE health_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- temporal
  recorded_at TIMESTAMPTZ NOT NULL,
  duration_seconds INT,               -- pour les ranges (session sommeil)
  
  -- type
  metric_type VARCHAR NOT NULL,       -- 'sleep_session' | 'steps' | 'heart_rate' | etc.
  
  -- value
  numeric_value NUMERIC,
  unit VARCHAR,
  
  -- source
  source VARCHAR NOT NULL,            -- 'health_connect' | 'manual' | 'lab' | 'dexcom'
  source_device VARCHAR,
  source_app VARCHAR,
  
  -- métadonnées riches
  metadata JSONB,
  
  -- déduplication
  source_record_id VARCHAR,
  ingested_at TIMESTAMPTZ DEFAULT NOW(),
  
  UNIQUE (source, source_record_id)
);

CREATE INDEX idx_health_metrics_type_time ON health_metrics(metric_type, recorded_at DESC);
CREATE INDEX idx_health_metrics_recorded ON health_metrics(recorded_at DESC);
CREATE INDEX idx_health_metrics_metadata ON health_metrics USING GIN (metadata);

-- Matérialisée pour daily summaries
CREATE MATERIALIZED VIEW daily_health_summary AS
SELECT 
  date_trunc('day', recorded_at) AS day,
  COALESCE(SUM(CASE WHEN metric_type='sleep_session' THEN duration_seconds END) / 3600.0, 0) AS sleep_hours,
  COALESCE(SUM(CASE WHEN metric_type='steps' THEN numeric_value END), 0) AS total_steps,
  AVG(CASE WHEN metric_type='heart_rate' THEN numeric_value END) AS hr_avg,
  MIN(CASE WHEN metric_type='heart_rate' THEN numeric_value END) AS hr_min,
  AVG(CASE WHEN metric_type='resting_hr' THEN numeric_value END) AS resting_hr,
  AVG(CASE WHEN metric_type='hrv_rmssd' THEN numeric_value END) AS hrv_rmssd_avg
FROM health_metrics
GROUP BY date_trunc('day', recorded_at);

CREATE TABLE health_markers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  measurement_date DATE NOT NULL,
  measurement_type VARCHAR,           -- 'blood_panel' | 'body_composition' | 'cgm_summary' | etc.
  source VARCHAR,
  
  values JSONB,
  normalized_metrics JSONB,
  
  fasting_state BOOLEAN,
  notes TEXT,
  attachment_path VARCHAR,
  
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 14.5 Tables Coaching / Suggestions

```sql
CREATE TABLE workout_suggestions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  generated_at TIMESTAMPTZ DEFAULT NOW(),
  for_date DATE,
  
  prompt_used TEXT,
  llm_response_raw JSONB,
  
  recommendation TEXT,
  reasoning TEXT,
  exercises JSONB,
  expected_duration_min INT,
  warnings JSONB,
  alternative_if_tired TEXT,
  
  status VARCHAR DEFAULT 'pending',   -- 'pending' | 'accepted' | 'modified' | 'rejected'
  user_feedback TEXT,
  user_modifications JSONB,
  
  tokens_used INT,
  cost_eur NUMERIC
);

CREATE TABLE nutrition_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  for_date DATE,
  generated_at TIMESTAMPTZ DEFAULT NOW(),
  
  daily_kcal_target INT,
  daily_protein_target_g INT,
  daily_carbs_target_g INT,
  daily_fats_target_g INT,
  hydration_target_l NUMERIC,
  
  meal_distribution JSONB,
  supplements_today JSONB,
  
  is_training_day BOOLEAN,
  notes TEXT
);

CREATE TABLE challenges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  week_start DATE,
  title VARCHAR,
  description TEXT,
  challenge_type VARCHAR,
  measurable_goal JSONB,
  tracking_method VARCHAR,            -- 'auto' | 'manual'
  xp_reward INT,
  deadline TIMESTAMPTZ,
  status VARCHAR DEFAULT 'active',    -- 'active' | 'completed' | 'failed' | 'expired'
  completed_at TIMESTAMPTZ,
  progress JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 14.6 Tables Gamification

```sql
CREATE TABLE missions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  for_date DATE,
  title VARCHAR,
  description TEXT,
  mission_type VARCHAR,
  xp_reward INT,
  status VARCHAR DEFAULT 'pending',   -- 'pending' | 'in_progress' | 'completed' | 'failed' | 'expired'
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE xp_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_type VARCHAR,                -- 'mission' | 'challenge' | 'pr' | etc.
  source_id UUID,
  xp_earned INT,
  notes TEXT,
  earned_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE user_level (
  id INT PRIMARY KEY DEFAULT 1,
  current_xp INT DEFAULT 0,
  current_level VARCHAR DEFAULT 'Recruit',
  total_xp_earned INT DEFAULT 0,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE streaks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  streak_type VARCHAR,                -- 'workout' | 'nutrition' | 'sleep'
  current_value INT DEFAULT 0,
  best_value INT DEFAULT 0,
  frozen_until DATE,
  freezes_used_this_month INT DEFAULT 0,
  last_calculated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (streak_type)
);
```

### 14.7 Tables Système / Auth

```sql
CREATE TABLE auth_attempts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ip_address INET,
  attempt_type VARCHAR,               -- 'login' | 'system_access'
  success BOOLEAN,
  attempted_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE agent_actions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_name VARCHAR,
  action_type VARCHAR,
  input JSONB,
  output JSONB,
  prompt_sent TEXT,
  llm_response_raw TEXT,
  tokens_used INT,
  cost_eur NUMERIC,
  duration_ms INT,
  status VARCHAR,                     -- 'success' | 'error' | 'partial'
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE agent_memory (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT,
  embedding VECTOR(1536),             -- pgvector
  tags VARCHAR[],
  source VARCHAR,                     -- 'explicit' | 'implicit' | 'manual'
  created_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ,
  is_obsolete BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_agent_memory_embedding ON agent_memory USING hnsw (embedding vector_cosine_ops);

CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_type VARCHAR,          -- 'direct_line' | 'coach_fitness'
  started_at TIMESTAMPTZ DEFAULT NOW(),
  last_message_at TIMESTAMPTZ
);

CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
  role VARCHAR,                       -- 'user' | 'assistant' | 'system'
  content TEXT,
  tokens_used INT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE llm_config (
  id INT PRIMARY KEY DEFAULT 1,
  navichat_model VARCHAR DEFAULT 'claude-sonnet-4-5',
  daily_call_budget INT DEFAULT 50,
  daily_cost_budget_eur NUMERIC DEFAULT 2.0,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE notification_config (
  id INT PRIMARY KEY DEFAULT 1,
  email_enabled BOOLEAN DEFAULT TRUE,
  push_enabled BOOLEAN DEFAULT TRUE,
  briefing_hour TIME DEFAULT '07:00',
  ntfy_topic VARCHAR,
  recipient_email VARCHAR,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 15. DONNÉES SEED (programme d'entraînement)

Le fichier `config/training_seed.yaml` initialise le programme PPL+Upper+Street de Frederick.

### Programme par jour

#### LUNDI — PUSH

| Exercice | Type | Baseline | Target | 1RM actuel → plateau |
|---|---|---|---|---|
| Bench Press (Barbell) | compound_free | 52.5kg × 7 | 70kg × 8 | 63 → 84 kg |
| DC incliné haltères | compound_free | 18kg/b × 9 | 24kg/b × 10 | ~50 → ~65 kg |
| Pec Deck | isolation | 43kg × 13 | 52-55kg × 15 | — |
| Shoulder Press Machine | compound_machine | 32kg × 12 | 40-43kg × 10 | — |
| Élévation latérale | isolation | 6kg/b × 15 | 10kg/b × 15 | — |
| Triceps Pushdown | isolation | 18kg × 11 | 25kg × 12 | — |
| Overhead Extension | isolation | 14kg × 12 | 20kg × 12 | — |

#### MARDI — PULL

| Exercice | Type | Baseline | Target | 1RM actuel → plateau |
|---|---|---|---|---|
| Rack Pull | compound_free | 90kg × 6 | 120kg × 6 | 107 → 143 kg |
| Lat Pulldown | compound_machine | 45kg × 10 | 60kg × 10 | — |
| Rowing Poulie V-bar | compound_machine | 43kg × 11 | 57-60kg × 12 | — |
| Rowing Haltère Unilat | compound_free | 20kg/b × 11 | 28-30kg/b × 10 | — |
| Face Pull | isolation | 20kg × 20 | 27-30kg × 20 | — |
| One-arm Cable Curl | isolation | 14kg/b × 12 | 18-20kg/b × 12 | — |
| Preacher Curl Machine | isolation | 18kg × 12 | 25kg × 12 | — |

#### MERCREDI — REPOS

#### JEUDI — LEGS

| Exercice | Type | Baseline | Target | 1RM actuel → plateau |
|---|---|---|---|---|
| Squat Barre | compound_free | 65kg × 7 | 85kg × 8 | 80 → 102 kg |
| Leg Press | compound_machine | 107kg × 10 | 160kg × 10 | — |
| Leg Extension | isolation | 39kg × 11 | 52-55kg × 12 | — |
| Leg Curl (rempl. RDL) | isolation | 50kg × 12 | 60-65kg × 12 | — |
| Leg Curl | isolation | 52kg × 10 | 65-68kg × 12 | — |
| Mollets Assis | isolation | 60kg × 18 | 75-80kg × 20 | — |
| Mollets Presse | isolation | 59kg × 15 | 75-80kg × 20 | — |

#### VENDREDI — UPPER

| Exercice | Type | Baseline | Target | Notes |
|---|---|---|---|---|
| DC incliné haltères | compound_free | 18kg/b × 9 | 24kg/b × 10 | même que push |
| Rowing Poulie V-bar | compound_machine | 39kg × 12 | 55kg × 12 | légèrement moins (fatigue) |
| Pec Deck | isolation | 39kg × 15 | 50-52kg × 15 | légèrement moins que push |
| Shoulder Press | compound_machine | 32kg × 12 | 40kg × 12 | même plateau que push |
| Lat Pulldown | compound_machine | 43kg × 12 | 57kg × 12 | légèrement moins que pull |
| Face Pull | isolation | 20kg × 17 | 27kg × 20 | même que pull |
| Superset Pushdown | isolation | 18kg × 10 | 25kg × 12 | même que push |
| Superset Curl Poulie | isolation | 20kg × 10 | 25kg × 12 | — |

#### SAMEDI — STREET WORKOUT

| Exercice | Type | Maintenant | Target | Timeline |
|---|---|---|---|---|
| Tractions Négatifs | calisthenics_progressive | 4×3 (5sec) | négatifs 4×5 (10sec) | 4 semaines |
| Tractions Assistées (bande) | calisthenics_progressive | pas encore | 3×5 (bande rouge) | 2-3 mois |
| Première Traction BW | calisthenics_progressive | 0 | 1 rep propre | ~4-5 mois (BW ~95kg) |
| Tractions Bodyweight | calisthenics_progressive | 0 | 3-5 reps | ~6-8 mois (BW ~90kg) |
| Pompes | calisthenics_progressive | 3×8 | 3×20 | 2-3 mois |
| Dips | calisthenics_progressive | 2-3 reps | 3×8 | 3-4 mois |

#### DIMANCHE — REPOS

### Bodyland transition (équipement spécialisé)

| Exercice machine | Poids départ | Plateau estimé |
|---|---|---|
| HS Chest Press | 40kg total (20/côté) | 70kg total (35/côté) |
| HS Incline Press | 30kg total (15/côté) | 50kg total (25/côté) |
| Panatta Hack Squat | 40kg plaques + chariot | 100-120kg plaques + chariot |
| HS Shoulder Press | 30kg total (15/côté) | 50kg total (25/côté) |
| HS Lat Pull | 30kg total (15/côté) | 50kg total (25/côté) |
| Watson/Atlantis Low Row | 30kg total (15/côté) | 50-55kg total (25-27/côté) |
| HS High Row | à tester | 45-50kg total |
| Leg Press HS/Panatta | 100-110kg | 180-200kg |

### Strength Standards (référentiel débutant → intermédiaire)

| Lift | Débutant | Plateau en déficit | Intermédiaire |
|---|---|---|---|
| Bench 1RM | 63 kg (0.6× BW) | 84 kg (0.88× BW à 95kg) | 100 kg (1.1× BW à 85kg) |
| Squat 1RM | 80 kg (0.76× BW) | 102 kg (1.07× BW à 95kg) | 130 kg (1.5× BW à 85kg) |
| Rack Pull 1RM | 107 kg (1.0× BW) | 143 kg (1.5× BW à 95kg) | 170 kg (2.0× BW à 85kg) |

### Contexte nutrition / supplements / sommeil

```yaml
training_context:
  phase: cutting
  phase_started_at: 2026-04-01
  current_weight_kg: 95
  
  # nutrition
  daily_kcal_target: 1650
  daily_protein_g_target_min: 180
  daily_protein_g_target_max: 200
  daily_hydration_l_target: 4
  
  # sommeil
  sleep_target_hours_min: 7
  sleep_target_hours_max: 9
  bedtime_target: "23:00"
  wakeup_target: "07:00"
  
  # NEAT
  daily_steps_target: 8000
  weekly_long_walks_target: 2
  
  # training
  weekly_session_target: 5
  active_split: "PPL+Upper+Street"
  
  supplements:
    - { name: "Creatine", dose: "5g", timing: "anytime", frequency: "daily" }
    - { name: "Whey", dose: "30g", timing: "post-workout", frequency: "training_days" }
    - { name: "Collagen", dose: "10g", timing: "morning", frequency: "daily" }
    - { name: "Omega-3", dose: "2g EPA+DHA", timing: "with_meal", frequency: "daily" }
    - { name: "Magnesium bisglycinate", dose: "300mg", timing: "evening", frequency: "daily" }
    - { name: "Vitamin D3", dose: "4000 IU", timing: "morning", frequency: "daily" }
    - { name: "Bioculture", dose: "1 capsule", timing: "morning", frequency: "daily" }
    - { name: "Multivitamin", dose: "1 tablet", timing: "morning", frequency: "daily" }
```

---

## 16. RÉCAP MOSCOW GLOBAL

### 🔴 MUST (sans ça, pas de projet)

```
US-001  Authentification au dashboard
US-002  Statut de l'agent en temps réel
US-003  Direct Line (chat temps réel)
US-004  Mémoire long-terme persistante
US-008  Synchronisation auto des workouts Hevy
US-010  Historique complet consolidé
US-012  Détection automatique des PRs
US-016  Suggestion du prochain workout
US-017  Plan nutritionnel adaptatif
US-025  Ingestion auto Health Connect via Tasker
```

### 🟡 SHOULD (important pour valeur perçue)

```
US-005   Historique des actions de l'agent
US-006a  Briefing par email
US-006b  Briefing push notification
US-007   Configuration paramètres LLM (zone System)
US-009   Synchronisation à la demande
US-011   État de récupération musculaire
US-013   Détection plateaus, régressions, behind schedule
US-013b  Tracking de progression vers les targets
US-014   Identification groupes musculaires négligés
US-015   Stats hebdo & mensuelles
US-018   Suggestions de meals contextuelles
US-019   Challenges hebdomadaires
US-020   Chat coach contextuel
US-022   Streaks d'entraînement
US-023   Missions journalières & XP
US-026   Daily health snapshot
US-027   Saisie manuelle de health markers
```

### 🟢 COULD (nice-to-have)

```
US-008b  Migration vers webhooks Hevy (Phase 4+)
US-008c  Sync bidirectionnelle Hevy (Phase 4+)
US-013c  Gestion de la transition d'équipement
US-021   Quick actions contextuelles dans le chat
US-024   Configuration des canaux de notification
```

### ❌ WON'T HAVE (this time)

```
App mobile native
Multi-user / public SaaS
Trading auto
STT (reconnaissance vocale)
Génération d'images / vidéos par l'agent
```

---

## 📊 STATISTIQUES DU PROJET

```
Total user stories                 : 33
Must                              : 10
Should                            : 17
Could                              : 5
Won't                             : (5 catégories)

Catégories couvertes               : 7
Tables de données planifiées       : 27
Intégrations externes              : 7 (Hevy, Cronometer, Anthropic, ntfy, Resend, Tasker/HC, Tailscale)
Durée Requirements Phase           : ~10 sessions de spec
Budget mensuel estimé              : 31-56€
Budget one-time                    : ~77€
Économies vs full-cloud            : ~700-900€
```

---

## 📝 PROCHAINES ÉTAPES

1. **Non-Functional Requirements (NFR)** — performance, sécurité, observability, scalability, reliability...
2. **Architecture détaillée** — diagramme C4, composants, contrats d'API
3. **Roadmap des phases** — Phase 0 (setup), 1 (MVP foundation), 2 (Hevy + brain), 3 (multi-agent + nutrition)
4. **Setup initial du repo** — structure, CI/CD, Docker, tooling
5. **Première ligne de code** 🚀

---

*Document généré le 17 mai 2026 — Frederick × Claude*
*Version : 1.0 (Requirements complete, NFR & Architecture en cours)*

