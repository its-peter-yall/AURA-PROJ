# Phase 09 — UI Review

**Audited:** 2026-05-23
**Baseline:** UI-SPEC.md
**Screenshots:** Not captured (no dev server running)

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 2/4 | Hardcoded strings deviate from the Copywriting Contract for empty, error, and destructive states. |
| 2. Visuals | 3/4 | Missing the specified elevated shadow on provider cards; icon-only button lacks aria-label in AURA-CHAT. |
| 3. Color | 3/4 | Active provider indicator uses semantic green instead of the reserved accent color. |
| 4. Typography | 4/4 | Good adherence to specified font weights and sizes. |
| 5. Spacing | 2/4 | Widespread use of non-scale arbitrary spacing (6px, 12px) breaking the 4px multiple rule. |
| 6. Experience Design | 3/4 | Excellent state coverage, but minor accessibility gaps. |

**Overall: 17/24**

---

## Top 3 Priority Fixes

1. **Copywriting Contract Violations** — User sees inconsistent wording across states — Update `ApiKeyManager.tsx` strings to match the UI-SPEC: change empty state text to "Configure an API key to access General Compute models.", error text to "Validation failed. Please check your API key.", and destructive confirmation to "Remove Key: Are you sure you want to remove this API key?".
2. **Spacing Scale Adherence** — Inconsistent layout rhythm — Replace non-scale Tailwind classes (`gap-1.5`, `p-3`, `mb-3`, `py-0.5`, `py-1.5`) across both `ProviderSettingsSection.tsx` and `ApiKeyManager.tsx` with scale-compliant 4px multiples (`gap-2`, `p-4`, `mb-4`, `py-1`, `py-2`).
3. **Card Elevation and Accent Color Application** — Flat visual hierarchy and incorrect active state coloring — Add `shadow-md` to the `ProviderCard` containers, and update the active provider indicator to use the accent color (`bg-primary/10 text-primary`) instead of `bg-green-500/10 text-green-500` to align with the visual contract.

---

## Detailed Findings

### Pillar 1: Copywriting (2/4)
- **AURA-CHAT/client/src/features/settings/components/ApiKeyManager.tsx:185** & **AURA-NOTES-MANAGER...:183**: Empty state body reads `"Enter an API key to enable models from {provider.label}."` instead of the contracted `"Configure an API key to access General Compute models."`.
- **AURA-CHAT/client/src/features/settings/components/ApiKeyManager.tsx:109** & **AURA-NOTES-MANAGER...:107**: Error state text falls back to `"Invalid key"` or `"Network error..."` instead of `"Validation failed. Please check your API key."`.
- **AURA-CHAT/client/src/features/settings/components/ApiKeyManager.tsx:158** & **AURA-NOTES-MANAGER...:156**: Destructive confirmation label uses `"Confirm Delete?"` instead of `"Remove Key: Are you sure you want to remove this API key?"`.
- Missing explicit `"No API key configured"` empty state heading.

### Pillar 2: Visuals (3/4)
- **AURA-CHAT/client/src/features/settings/components/ProviderSettingsSection.tsx:84** & **AURA-NOTES-MANAGER...:82**: The `ProviderCard` container lacks an elevated shadow. Spec demands an elevated shadow on provider cards.
- **AURA-CHAT/client/src/features/settings/components/ApiKeyManager.tsx:196**: The `<button>` for showing/hiding the API key (Eye/EyeOff icon) lacks an `aria-label` or tooltip, which was correctly implemented in AURA-NOTES-MANAGER but missed here.

### Pillar 3: Color (3/4)
- **AURA-CHAT/client/src/features/settings/components/ProviderSettingsSection.tsx:96** & **AURA-NOTES-MANAGER...:96**: Active status badge uses `text-green-500 bg-green-500/10`. The UI-SPEC reserves the accent color (`bg-cyber-yellow-400` / primary) for "Active selected provider cards".

### Pillar 4: Typography (4/4)
- Font weights (`font-semibold`, `font-bold`) and sizes (`text-xs`, `text-sm`, `text-base`, `text-2xl`) align well with the specification.
- No arbitrary text sizes (`text-[13px]`) were found. Hierarchy is clear.

### Pillar 5: Spacing (2/4)
- Multiple violations of the 4px multiple spacing scale across both frontend packages:
  - `gap-1.5` (6px) used in active/no-key badges and buttons.
  - `mb-3` (12px) used in `ProviderCard` headers.
  - `p-3` (12px) used in the masked key display container.
  - `py-0.5` (2px) used in configured/not configured badges.
  - `py-1.5` (6px) used in Validate and Delete buttons.

### Pillar 6: Experience Design (3/4)
- Loading states (skeletons with `animate-pulse`) and disabled states during mutations are thoroughly implemented.
- Destructive actions successfully enforce a two-step confirmation pattern (`isConfirmingDelete`).
- One minor gap in AURA-CHAT accessibility (missing `aria-label` on the password visibility toggle).

---

## Files Audited
- `AURA-CHAT/client/src/types/settings.ts`
- `AURA-CHAT/client/src/features/settings/components/ProviderSettingsSection.tsx`
- `AURA-CHAT/client/src/features/settings/components/ApiKeyManager.tsx`
- `AURA-NOTES-MANAGER/frontend/src/types/settings.ts`
- `AURA-NOTES-MANAGER/frontend/src/features/settings/components/ProviderSettingsSection.tsx`
- `AURA-NOTES-MANAGER/frontend/src/features/settings/components/ApiKeyManager.tsx`