# Phase 1: Multi-model Chat Configuration - UI Specification

## 1. Overview
This UI specification defines the changes required for Phase 1: Multi-model chat configuration. 
The goal is to provide AURA administrators with a dedicated settings interface for configuring an array of 1 to 5 allowed chat models, while designating one as the default. The user-facing chat application will respect this restricted list and the default model selection.

## 2. Visual Specifications

### Colors and Styling
- **Theme**: Relies tightly on the existing Tailwind utility classes and CSS variables (e.g., `bg-card`, `bg-primary`, `text-muted-foreground`, `border-border/50`).
- **Typography**: Adheres to existing font sans specifications. Small secondary text will use `text-xs` (12px) and primary labels `text-sm` (14px).
- **Icons (`lucide-react`)**: 
  - `Star` / `Check` to indicate the default model.
  - `Trash2` or `X` for removing a model from the list.
  - `GripVertical` for dragging/reordering indicators.

### Layout Details
- **Settings Section (`ChatModelsSection`)**:
  - The "Chat Model" entry inside the `DefaultModelSection` list will be replaced/extended.
  - Will display an active list of selected models (1-5 limit) vertically using flexbox (`flex-col`, `space-y-2`).
  - Below the active list, a `<HierarchicalModelPicker>` acts as the input to add new models, disabled when the list size reaches 5.
- **List Items (Selected Models)**:
  - Each item is a horizontal flex row (`items-center`, `justify-between`) within a stylized card format (`p-3 bg-card/50 rounded-md border border-border/10`).
  - Contains drag handle, model name (`font-semibold`), "Default" indicator/button, and a delete action.

## 3. Interaction Specifications

### Selected Model List States
- **Hover**: List items show a subtle background color shift (e.g., `hover:bg-card`). Interactive icons slightly increase opacity.
- **Default Selection**: Clicking "Set as Default" on a non-default model updates the `default_index` immediately in the UI state.
- **Delete**: Removes a model. If the deleted model was the default, the `default_index` automatically shifts to the first remaining model (`index 0`). If only 1 model is left, the delete button is disabled. 

### Add Model Picker
- **Max capacity**: When the selected models array reaches 5 length, the `HierarchicalModelPicker` for adding new models becomes visually subdued (opacity-50) and blocks pointer events (disabled).

### Chat Page Picker (`InlineModelPicker`)
- Renders identical to before, but since `allowedModels` limits the displayed choices, users only see up to 5 models.
- If a user starts a new session, the chat page will utilize the "Default Model" defined in the settings config to pre-populate the active picker state.

## 4. Component Inventory

### New Components
1. **`ChatModelsSection`** (`features/settings/components/ChatModelsSection.tsx`)
   - Replaces the generic `UseCaseSection` loop behavior for the 'chat' use case inside `DefaultModelSection.tsx`.
   - Manages state for `selectedModels` array and `defaultIndex`.
   - Utilizes `framer-motion` for smooth additions/removals from the list.

### Modified Components
1. **`DefaultModelSection`** (`features/settings/components/DefaultModelSection.tsx`)
   - Updated to fork the rendering logic: renders `ChatModelsSection` for the `chat` use case, and the standard `UseCaseSection` for all others (embeddings, etc).
2. **`ChatPage`** (`features/chat/ChatPage.tsx` or where default model selection occurs)
   - Must intercept the `/chat/config` API response to initialize the `sessionModel` default to the new `default_model` value instead of always pulling from hardcoded fallbacks if no existing session model exists.
3. **`InlineModelPicker`** (`features/chat/components/InlineModelPicker.tsx`)
   - Existing component handles `allowedModels` via `useMemo` filtering. Re-verify the filter accommodates vendor parsing properly. Ensure if `isReadOnly` is triggered (only 1 allowed model), it displays elegantly without a dropdown arrow.

## 5. Animation Specifications

- **List Item Reorder/Remove**: Add `framer-motion` `<AnimatePresence>` around the list mapping in `ChatModelsSection`.
  - Adding item: `initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}`
  - Removing item: `exit={{ opacity: 0, scale: 0.95 }}`
  - Layout transitions: Enable `<motion.div layout>` to allow remaining list items to smoothly slide into their new positions when an item is removed.

## 6. Responsive Behavior

- **Mobile View (< 640px)**:
  - Settings models list collapses paddings slightly (`px-2 py-2`).
  - Button text for "Set as Default" might become just an icon (`Star`) to conserve horizontal space.
- **Desktop View (>= 640px)**:
  - Full text labels remain visible.
  - Hover states on drag handles and delete buttons become active.

## 7. Accessibility Requirements

- **Keyboard Navigation**:
  - All interactive items (remove button, set default button) must be accessible via `Tab` indexing.
  - Support `Enter` / `Space` to activate.
- **Screen Readers**:
  - Add `aria-label` to the drag handles (if implemented), delete buttons, and default toggles.
  - Example: `aria-label="Remove model gemini-1.5-flash"`.
- **Validation Constraints**: 
  - Screen reader announcements using `aria-live="polite"` should announce when the 5-model limit is reached.

## 8. Acceptance Criteria

- [ ] `DefaultModelSection` successfully renders the new `ChatModelsSection` exclusively for the `chat` use case.
- [ ] Users can add up to 5 models to the chat configuration list.
- [ ] Users cannot add a 6th model; UI provides visual feedback that the limit is reached.
- [ ] Users can toggle which of the selected models acts as the default model.
- [ ] Users can delete a model from the list. If it was the default, default safely re-assigns to index 0.
- [ ] If list drops to 1 item, the delete action is disabled (to ensure minimum 1 model requirement).
- [ ] Changes are saved to the backend API (`useUpdateChatModels` mutation).
- [ ] Chat UI initializes new sessions using the specified default model.
- [ ] Chat UI's `InlineModelPicker` displays only the admin-configured allowed models (1-5 limit).
