I will upgrade the `ModuleSelectorModal` to support multi-document selection, allowing you to select specific subsets of documents for your chat sessions.

### 1. Update `ModuleSelectorModal.tsx`
-   **Refactor State**: Change `documentId` (single string) to `documentIds` (string array) to store multiple selections.
-   **Update Logic**:
    -   Modify `handleDocumentClick` to **toggle** document IDs in the array (add if missing, remove if present).
    -   Update `saveSelection` and `loadStoredSelection` to persist the array of IDs.
    -   Update the "Confirm" button logic to validate that at least one document is selected.
    -   Update the button label to show the count of selected documents (e.g., "3 Documents Selected").
-   **Update UI**:
    -   Change the visual indicator from a radio-style check to a multi-select style (highlighting all selected items).
    -   Update the props interface to pass `string[]` instead of `string` to the parent.

### 2. Update `ChatPage.tsx`
-   **Refactor State**: Change `selectedDocumentId` to `selectedDocumentIds`.
-   **Update Handlers**:
    -   Update `handleCreateSession` to pass the full list of selected document IDs to the backend API (which already supports lists).
    -   Update the `ModuleSelectorModal` callback to handle the list of IDs.

### 3. Verification
-   Verify that clicking multiple documents highlights them all.
-   Verify that the "Confirm" button works with multiple selections.
-   Verify that creating a session sends the correct list of IDs to the backend.
