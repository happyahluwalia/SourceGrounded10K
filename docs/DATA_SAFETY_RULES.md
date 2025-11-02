# 🛡️ DATA SAFETY RULES - CRITICAL

**INCIDENT**: November 2, 2025 - Recommended `docker system prune -a` which destroyed:
- All PostgreSQL tables (checkpoints, filings, chunks)
- All Qdrant vectors (processed SEC filings)
- All Ollama models (llama3.1, gemma3:1b, nomic-embed-text)
- Production site completely down

**LESSON**: Never recommend destructive commands without explicit warnings and user confirmation.

---

## 🚨 ABSOLUTE PROHIBITIONS

### NEVER Recommend These Commands Without Explicit User Request:

```bash
# ❌ FORBIDDEN - Destroys everything
docker system prune -a
docker system prune --volumes
docker volume prune
docker volume rm

# ❌ FORBIDDEN - Destroys data
rm -rf data/
rm -rf *.db
DROP DATABASE
TRUNCATE TABLE

# ❌ FORBIDDEN - Destroys containers with data
docker-compose down -v
docker rm -f $(docker ps -aq)
```

---

## ✅ SAFE ALTERNATIVES

### Instead of `docker system prune -a`:

```bash
# ✅ SAFE - Only removes stopped containers
docker container prune

# ✅ SAFE - Only removes unused images (keeps running)
docker image prune

# ✅ SAFE - Only removes dangling images
docker image prune --filter "dangling=true"

# ✅ SAFE - Removes build cache only
docker builder prune
```

### Instead of `docker-compose down -v`:

```bash
# ✅ SAFE - Stops containers but preserves volumes
docker-compose down

# ✅ SAFE - Restart services
docker-compose restart
```

---

## ⚠️ REQUIRED WARNINGS

Before ANY destructive command, MUST include:

```markdown
⚠️ **WARNING: DATA LOSS RISK**

This command will delete:
- [ ] List what will be deleted
- [ ] Estimate recovery time
- [ ] Provide backup instructions

**Backup first:**
```bash
# Provide backup commands
```

**Are you sure? Type 'yes' to confirm.**
```

---

## 🔒 PRODUCTION DATA PROTECTION

### Before Recommending ANY Command:

1. **Check if it affects data**
   - Database operations?
   - Volume operations?
   - File deletions?

2. **Check environment**
   - Is this production?
   - Are volumes in use?
   - Is data backed up?

3. **Provide safe alternative first**
   - Always suggest non-destructive option
   - Explain why it's safer
   - Only mention destructive as last resort

4. **Require explicit confirmation**
   - User must type "yes" or confirm
   - Explain consequences clearly
   - Provide rollback plan

---

## 📋 CHECKLIST: Before Destructive Commands

- [ ] Is there a safer alternative?
- [ ] Did I warn about data loss?
- [ ] Did I explain what will be deleted?
- [ ] Did I provide backup instructions?
- [ ] Did I provide recovery steps?
- [ ] Did I get explicit user confirmation?
- [ ] Did I document the risks?

**If ANY checkbox is unchecked → DO NOT RECOMMEND THE COMMAND**

---

## 🎯 SPECIFIC SCENARIOS

### Scenario: "Docker is using too much space"

**❌ WRONG:**
```bash
docker system prune -a  # Destroys everything
```

**✅ RIGHT:**
```bash
# Check what's using space first
docker system df

# Remove only build cache (safe)
docker builder prune

# Remove stopped containers (safe)
docker container prune

# Remove unused images (safe, keeps running)
docker image prune
```

### Scenario: "Need to rebuild containers"

**❌ WRONG:**
```bash
docker-compose down -v  # Destroys volumes!
docker-compose build --no-cache
```

**✅ RIGHT:**
```bash
# Rebuild without destroying data
docker-compose build --no-cache
docker-compose up -d
```

### Scenario: "Database issues"

**❌ WRONG:**
```bash
docker volume rm postgres_data  # Destroys all data!
```

**✅ RIGHT:**
```bash
# Backup first
docker exec postgres pg_dump -U user db > backup.sql

# Then investigate issue
docker-compose logs postgres
docker-compose restart postgres
```

---

## 🔄 RECOVERY PROCEDURES

### If Data Loss Occurs:

1. **Immediate Assessment**
   ```bash
   # Check what survived
   docker volume ls
   docker exec postgres psql -U user -d db -c "\dt"
   curl http://qdrant:6333/collections
   ```

2. **Document Loss**
   - What was deleted
   - When it happened
   - What command caused it
   - Estimated recovery time

3. **Recovery Steps**
   - Restore from backups (if available)
   - Recreate database schema
   - Reprocess data from source
   - Pull required models

4. **Prevention**
   - Add to this document
   - Create backup procedures
   - Implement safeguards

---

## 💾 BACKUP REQUIREMENTS

### Before ANY Destructive Operation:

```bash
# 1. Backup PostgreSQL
docker exec postgres pg_dump -U user db > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Backup Qdrant (if possible)
curl http://qdrant:6333/collections/collection_name/snapshots -X POST

# 3. List volumes
docker volume ls > volumes_backup.txt

# 4. Export important data
# (Add specific backup commands for your application)
```

---

## 🎓 TEACHING MOMENTS

### When Suggesting Docker Commands:

**Always explain:**
1. What the command does
2. What it affects
3. What's the risk
4. What's the alternative
5. How to recover if something goes wrong

**Example:**
```markdown
To clean up Docker space, use:

```bash
docker image prune
```

**What it does:** Removes unused images (not attached to containers)
**Risk:** Low - only removes images you can re-download
**Alternative:** `docker system df` to check space first
**Recovery:** Re-pull images with `docker pull`
```

---

## 🚨 INCIDENT RESPONSE

### If You Recommend a Destructive Command:

1. **Immediate acknowledgment**
   - Apologize
   - Take responsibility
   - Don't make excuses

2. **Assess damage**
   - What was lost
   - What survived
   - Recovery time estimate

3. **Provide recovery plan**
   - Step-by-step instructions
   - Estimated time for each step
   - Alternative approaches

4. **Update rules**
   - Add to this document
   - Create safeguards
   - Prevent recurrence

5. **Document lesson**
   - What went wrong
   - Why it happened
   - How to prevent it

---

## 📝 COMMAND APPROVAL MATRIX

| Command Type | Risk Level | Required Actions |
|-------------|------------|------------------|
| `docker container prune` | 🟢 Low | None - safe |
| `docker image prune` | 🟢 Low | None - safe |
| `docker builder prune` | 🟢 Low | None - safe |
| `docker-compose restart` | 🟢 Low | None - safe |
| `docker-compose down` | 🟡 Medium | Warn about container loss |
| `docker system prune` | 🟠 High | Warn + backup + confirm |
| `docker system prune -a` | 🔴 CRITICAL | **NEVER without explicit request** |
| `docker volume rm` | 🔴 CRITICAL | **NEVER without explicit request** |
| `docker-compose down -v` | 🔴 CRITICAL | **NEVER without explicit request** |
| `DROP DATABASE` | 🔴 CRITICAL | **NEVER without explicit request** |

---

## ✅ SAFE COMMANDS (Always OK)

```bash
# Viewing/Inspecting (always safe)
docker ps
docker images
docker volume ls
docker system df
docker-compose logs
docker inspect

# Non-destructive operations
docker-compose up -d
docker-compose restart
docker-compose build
docker exec -it container bash

# Cleaning (safe)
docker container prune
docker image prune
docker builder prune
```

---

## 🎯 GOLDEN RULE

**"When in doubt, DON'T recommend it. Ask the user first."**

If a command:
- Deletes data
- Removes volumes
- Drops databases
- Truncates tables
- Removes files

→ **STOP. WARN. CONFIRM. BACKUP.**

---

## 📚 REQUIRED READING

Before recommending ANY Docker command, review:
1. This document
2. Docker compose file (check for volumes)
3. Current environment (dev vs prod)
4. User's backup status

---

**Last Updated**: November 2, 2025  
**Incident**: Docker prune destroyed production data  
**Status**: Active - MUST be followed  
**Severity**: CRITICAL - Data loss prevention
