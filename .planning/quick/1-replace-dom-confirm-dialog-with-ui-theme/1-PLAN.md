---
phase: quick
plan: 1
type: execute
wave: 1
depends_on: []
files_modified: ["AURA-NOTES-MANAGER/frontend/src/pages/AdminDashboard.tsx"]
autonomous: true
must_haves:
  truths:
    - "User can click delete to open a themed confirmation dialog"
    - "User can cancel deletion in the dialog without deleting the user"
    - "User can confirm deletion in the dialog to actually delete the user"
  artifacts:
    - path: "AURA-NOTES-MANAGER/frontend/src/pages/AdminDashboard.tsx"
      provides: "User management UI with themed delete confirmation"
      contains: "<ConfirmDialog"
  key_links:
    - from: "AURA-NOTES-MANAGER/frontend/src/pages/AdminDashboard.tsx"
      to: "AURA-NOTES-MANAGER/frontend/src/components/ui/ConfirmDialog.tsx"
      via: "import and render"
      pattern: "import \\{ ConfirmDialog \\}"
---

<objective>
Replace the native DOM confirm dialog with the themed ConfirmDialog component when deleting a user in the Admin Dashboard.
Purpose: Improve UX by using a consistent, themed confirmation dialog instead of a boring browser popup.
Output: AdminDashboard.tsx updated to use the existing ConfirmDialog component for user deletion.
</objective>

<execution_context>
@C:/Users/Peter/.config/opencode/get-shit-done/workflows/execute-plan.md
@C:/Users/Peter/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@AURA-NOTES-MANAGER/frontend/src/pages/AdminDashboard.tsx
@AURA-NOTES-MANAGER/frontend/src/components/ui/ConfirmDialog.tsx
</context>

<tasks>

<task type="auto">
  <name>Task 1: Replace native confirm with ConfirmDialog</name>
  <files>AURA-NOTES-MANAGER/frontend/src/pages/AdminDashboard.tsx</files>
  <action>
    - Import `ConfirmDialog` from `../components/ui/ConfirmDialog`.
    - Add a state variable `const [userToDelete, setUserToDelete] = useState<string | null>(null);` to the `AdminDashboard` component.
    - Change the existing `handleDeleteUser` to `confirmDeleteUser` and remove the `if (!confirm(...))` check. Update it to use `userToDelete` instead of the `userId` parameter. At the end (in a `finally` block or after success/catch), call `setUserToDelete(null)`.
    - Create a new `handleDeleteUser` function that takes `userId: string` and just sets it: `setUserToDelete(userId)`.
    - Add the `<ConfirmDialog />` component at the bottom of the `AdminDashboard` component return block (just before the closing `</div>` or `<style>` block), passing the required props: `isOpen={!!userToDelete}`, `title="Delete User"`, `message="Are you sure you want to delete this user? This action cannot be undone."`, `confirmLabel="Delete"`, `variant="danger"`, `destructive={true}`, `onConfirm={confirmDeleteUser}`, and `onCancel={() => setUserToDelete(null)}`.
  </action>
  <verify>
    npm run build in AURA-NOTES-MANAGER/frontend to ensure it compiles without type errors.
  </verify>
  <done>
    Clicking delete on a user opens a themed `ConfirmDialog` and confirming it triggers the actual deletion logic.
  </done>
</task>

</tasks>

<verification>
Check that the `ConfirmDialog` is successfully rendered and the user list refreshes correctly upon confirming deletion.
</verification>

<success_criteria>
The native browser popup `confirm()` for user deletion is completely replaced by `<ConfirmDialog />`.
</success_criteria>

<output>
After completion, create `.planning/quick/1-replace-dom-confirm-dialog-with-ui-theme/1-SUMMARY.md`
</output>
