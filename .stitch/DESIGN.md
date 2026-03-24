# SurePay Design System

## 1. Visual Identity

### Color Palette

**Primary Colors:**
- Primary: `#0066FF` (Trust Blue)
- Primary Dark: `#0052CC`
- Primary Light: `#E6F0FF`

**Semantic Colors:**
- Success: `#10B981` (Green for payouts)
- Warning: `#F59E0B` (Amber for pending)
- Error: `#EF4444` (Red for disputes)
- Info: `#3B82F6` (Blue for info)

**Neutral Colors:**
- Background: `#FAFBFC`
- Surface: `#FFFFFF`
- Border: `#E5E7EB`
- Text Primary: `#111827`
- Text Secondary: `#6B7280`
- Text Tertiary: `#9CA3AF`

**Dark Mode:**
- Background: `#0F172A`
- Surface: `#1E293B`
- Text Primary: `#F8FAFC`
- Text Secondary: `#94A3B8`

### Typography

**Font Family:**
- Primary: `Satoshi, system-ui, sans-serif`
- Fallback: `-apple-system, BlinkMacSystemFont, sans-serif`

**Scale:**
- Display: 48px / 700 weight / -0.02em tracking
- H1: 36px / 700 weight / -0.01em tracking
- H2: 28px / 600 weight / 0 tracking
- H3: 22px / 600 weight / 0 tracking
- Body Large: 18px / 400 weight
- Body: 16px / 400 weight
- Body Small: 14px / 400 weight
- Caption: 12px / 500 weight / 0.02em tracking

## 2. Components

### Buttons

**Primary Button:**
- Background: `#0066FF`
- Text: White
- Padding: 14px 24px
- Border Radius: 8px
- Font: 16px / 600 weight
- Hover: Scale 1.02, shadow
- Active: Scale 0.98

**Secondary Button:**
- Background: White
- Border: 2px solid `#E5E7EB`
- Text: `#111827`
- Hover: Background `#F9FAFB`

**Ghost Button:**
- Background: Transparent
- Text: `#0066FF`
- Hover: Background `#E6F0FF`

### Cards

**Standard Card:**
- Background: White
- Border Radius: 12px
- Border: 1px solid `#E5E7EB`
- Shadow: 0 1px 3px rgba(0,0,0,0.1)
- Padding: 24px

**Elevated Card:**
- Shadow: 0 4px 6px -1px rgba(0,0,0,0.1)
- Hover: Shadow 0 10px 15px -3px rgba(0,0,0,0.1)

### Inputs

**Text Input:**
- Border: 1px solid `#E5E7EB`
- Border Radius: 8px
- Padding: 12px 16px
- Font: 16px
- Focus: Border `#0066FF`, shadow
- Error: Border `#EF4444`

### Status Badges

- `FUNDS_LOCKED`: Blue badge with lock icon
- `AWAITING_CONFIRMATION`: Amber badge with clock
- `RELEASED`: Green badge with checkmark
- `DISPUTED`: Red badge with warning

## 3. Layout

### Spacing Scale
- 4px, 8px, 12px, 16px, 20px, 24px, 32px, 40px, 48px, 64px, 96px

### Container
- Max Width: 1200px
- Padding: 24px mobile, 32px tablet, 48px desktop

### Grid
- 12-column grid
- Gutter: 24px
- Breakpoints: 640px, 768px, 1024px, 1280px

## 4. Animations & Interactions

### Micro-interactions
- Button hover: Scale 1.02, duration 200ms, ease-out
- Card hover: Shadow increase, duration 300ms
- Status change: Fade in + scale, duration 400ms
- Toast notification: Slide in + fade, duration 300ms

### Page Transitions
- Initial load: Fade in, duration 600ms
- Route change: Slide + fade, duration 300ms

### Loading States
- Skeleton: Shimmer animation
- Spinner: Rotate 360deg, duration 1s, linear
- Progress: Fill from left, duration proportional

## 5. Nigerian Market Considerations

### Mobile-First Design
- Touch targets minimum 48px
- Swipe gestures for common actions
- Bottom navigation on mobile
- Thumb-friendly button placement

### Trust Signals
- Bank logos prominently displayed
- Paystack badge on checkout
- Security icons (lock, shield)
- Transaction ID visible

### Performance
- Images optimized for slow networks
- Progressive loading
- Offline support indicators

## 6. Design System Notes for Stitch Generation

When generating pages with Stitch:

**Color Usage:**
- Use Primary Blue (#0066FF) for CTAs and trust elements
- Use Green (#10B981) for success states and payouts
- Keep backgrounds light (#FAFBFC) for readability

**Typography:**
- Large, clear headings (36px+ for hero)
- Readable body text (16px minimum)
- Bold weights (600+) for important info

**Components:**
- Rounded corners (8px-12px) for friendly feel
- Subtle shadows for depth
- Clear visual hierarchy

**Layout:**
- Single column on mobile
- Clear spacing between sections
- Sticky header for navigation

**Imagery:**
- Real Nigerian scenes when possible
- Diverse representation
- Product photography for featured items
- Icons from Lucide or similar

**Key Principles:**
- Trust over flashiness
- Clarity over cleverness
- Speed over complexity
- Mobile over desktop
