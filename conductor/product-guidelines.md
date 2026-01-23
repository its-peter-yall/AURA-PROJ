# AURA Product Guidelines

> **Version:** 1.0
> **Type:** Design and Brand Guidelines

## Tone of Voice

### AI Assistant Responses (AURA-CHAT)

All AI-generated responses in AURA-CHAT must follow a **Friendly/Educational** tone:

- **Approachable**: Use warm, welcoming language that encourages learning
- **Explanatory**: Provide context and explanations, not just answers
- **Encouraging**: Acknowledge good questions and progress
- **Patient**: Assume the user is learning, not an expert

### Examples

| Avoid | Preferred |
|-------|-----------|
| "The answer is X." | "Great question! The answer is X. Here's why..." |
| "That's incorrect." | "Let me help clarify that. What you found is related, but..." |
| "Use function Y." | "You can solve this with function Y. Let me walk you through how it works..." |

### Response Structure

1. **Acknowledge**: Validate the user's question
2. **Answer**: Provide the core answer
3. **Explain**: Add context or reasoning
4. **Extend**: Offer related concepts or next steps

## Visual Identity

### Color Palette

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| **Primary** | Cyber Yellow | `#FFD400` | Buttons, links, accents, highlights |
| **Background** | Deep Black | `#0A0A0A` | Main application background |
| **Surface** | Dark Gray | `#1A1A1A` | Cards, panels, modals |
| **Text Primary** | Off White | `#F5F5F5` | Primary text content |
| **Text Secondary** | Light Gray | `#A0A0A0` | Secondary text, labels |
| **Success** | Green | `#10B981` | Success states, confirmations |
| **Error** | Red | `#EF4444` | Error states, alerts |
| **Warning** | Orange | `#F59E0B` | Warning states |

### Typography

- **Primary Font**: Inter or system sans-serif
- **Code Font**: JetBrains Mono or Fira Code
- **Base Size**: 16px (1rem)
- **Line Height**: 1.6 for body text

### Component Styling

- **Border Radius**: 8px for cards, 4px for buttons
- **Shadows**: Subtle shadows for depth (no harsh borders)
- **Animations**: Smooth transitions (200-300ms ease-out)

## Accessibility Guidelines

### Standard Compliance

AURA targets **WCAG 2.1 Level AA** compliance, the industry standard for educational platforms and required by ADA Title II for public education institutions.

### Core Principles (POUR)

1. **Perceivable**: Content must be presentable in ways users can perceive
2. **Operable**: Interface components must be operable
3. **Understandable**: Information and operation must be understandable
4. **Robust**: Content must be robust enough for reliable interpretation

### Implementation Requirements

| Requirement | Implementation |
|-------------|----------------|
| **Keyboard Navigation** | All interactive elements accessible via Tab, Enter, Space, Arrow keys |
| **Screen Reader Support** | Semantic HTML, ARIA labels, descriptive alt text |
| **Focus Indicators** | Visible focus ring (Cyber Yellow `#FFD400`) on all interactive elements |
| **Color Contrast** | Minimum 4.5:1 for normal text, 3:1 for large text |
| **Skip Links** | "Skip to main content" link for keyboard users |
| **Error Handling** | Clear error messages with suggestions, no error-only color cues |
| **Form Labels** | All form inputs have associated labels |

### Testing Checklist

- [ ] Run keyboard-only navigation through all flows
- [ ] Test with screen reader (NVDA, VoiceOver, or equivalent)
- [ ] Verify color contrast ratios meet WCAG AA standards
- [ ] Check all images have descriptive alt text
- [ ] Ensure error messages are clear and actionable

## Brand Messaging

### Voice Characteristics

- **Clear**: Avoid jargon unless necessary; explain technical terms
- ** Helpful**: Focus on user success and learning outcomes
- **Professional**: Maintain credibility without being cold
- **Inclusive**: Use inclusive language, avoid assumptions about users

### Terminology Guidelines

| Use | Avoid |
|-----|-------|
| "Study session" | "Chat session" |
| "Module" | "Collection" or "Folder" |
| "Knowledge graph" | "Graph view" or "Nodes" |
| "Documents" | "Files" or "Materials" |

### Error Messages

| Avoid | Preferred |
|-------|-----------|
| "Error 500" | "Something went wrong on our end. Please try again." |
| "Invalid input" | "Please check your entry and try again." |
| "Access denied" | "You don't have permission to access this module." |

## UI Component Guidelines

### Buttons

- **Primary**: Cyber Yellow background, black text
- **Secondary**: Transparent background, white border, white text
- **Danger**: Red background, white text
- All buttons must have visible focus state

### Cards

- Dark gray background (`#1A1A1A`)
- 8px border radius
- Subtle shadow on hover
- Cyber yellow focus ring

### Forms

- Labels above inputs
- Clear error states with helper text
- Required field indicators
- Autofocus on first field

### Notifications

- **Success**: Green toast, top-right
- **Error**: Red toast, top-right
- **Info**: Blue toast, top-right
- **Warning**: Orange toast, top-right

## Developer Notes

### CSS Variables

```css
:root {
  --color-primary: #FFD400;
  --color-bg-primary: #0A0A0A;
  --color-bg-surface: #1A1A1A;
  --color-text-primary: #F5F5F5;
  --color-text-secondary: #A0A0A0;
  --color-success: #10B981;
  --color-error: #EF4444;
  --color-warning: #F59E0B;
  --radius-sm: 4px;
  --radius-md: 8px;
}
```

### Tailwind Configuration

The project uses TailwindCSS. Configure cyber yellow as:

```javascript
colors: {
  primary: '#FFD400',
  // ... other colors
}
```

### File Headers

All new code files must include descriptive headers per CLAUDE.md standards.
