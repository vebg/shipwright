# Discovery interview — sample-bakery (2026-10-19)
Sample answers (fictional) showing what the intake produces.

## 1. The product
- One paragraph: A small bakery takes cake orders for pickup; customers choose a cake, a size and a pickup slot from their phone; the owner sees and confirms orders from hers.
- Users: general public (customers, low technical comfort); the owner (staff).
- Today: WhatsApp messages and a paper notebook; double bookings of the oven are the problem.
- Success: no more double-booked pickup slots in the first month.

## 2. Surfaces and reach
- Surfaces: customer app (iOS/Android), web admin for the owner, API.
- Language: Spanish; Dominican Republic; one time zone; prices in DOP.
- Realtime: the admin sees new orders without refreshing; push to the customer when the order is confirmed.

## 3. Inspiration and references
| Reference | Kind | What to take | What NOT to take |
|---|---|---|---|
| (a bakery app link) | link | the slot picker | the loyalty program |

## 4. Technology and constraints
- Decided: Flutter for the customer app. Open: API and admin stack — planner proposes.
- Constraints: no payments in v1 (pay at pickup); privacy policy for the stores.

## 5. Brand and design
- Brand: logo exists (design/inbox/), no palette; tone: warm, simple, big buttons.

## 6. Working agreement
- Tests: none — manual verification with evidence (the owner reviews deliverables).
- Layout: two repositories (platform, apps). Updates: terminal + Telegram, in Spanish. Budget: US$300.
- Out of scope v1: payments, delivery, loyalty.
