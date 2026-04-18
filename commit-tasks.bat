@echo off
cd /d "D:\Peter\AURA Twin Proj\AURA-PROJ"

echo === Task 1: Types ===
git add AURA-CHAT/client/src/types/settings.ts
git commit -m "feat: add ChatModelEntry and ChatModelsConfig types for multi-model chat configuration"

echo === Task 2: API functions ===
git add AURA-CHAT/client/src/features/settings/api/settingsApi.ts
git commit -m "feat: add fetchChatModelsConfig and updateChatModels API functions"

echo === Task 3: Hooks ===
git add AURA-CHAT/client/src/features/settings/hooks/useSettingsApi.ts
git commit -m "feat: add useChatModelsConfig and useUpdateChatModels TanStack Query hooks"

echo === Task 4: ChatModelsSection component ===
git add AURA-CHAT/client/src/features/settings/components/ChatModelsSection.tsx
git commit -m "feat: create ChatModelsSection component for multi-model chat configuration"

echo === Task 5: DefaultModelSection modification ===
git add AURA-CHAT/client/src/features/settings/components/DefaultModelSection.tsx
git commit -m "feat: render ChatModelsSection for chat use case in DefaultModelSection"

echo === All commits complete ===
git log --oneline -5
