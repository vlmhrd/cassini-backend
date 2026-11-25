# The Case: Photo and Location Proof Is Automation's Weak Spot

> **Automated systems increasingly accept a photo and a location as proof. Both can now be faked cheaply. So the proof that automation depends on has become its weakest point.**

## 1. Automation runs on photo and location proof

Human checks are being replaced by automated ones, and those rely on two inputs: *a photo* and *where it was taken*.

- **Deliveries:** a doorstep photo closes the order, with no human reviewing it.
- **Mobility:** an end-of-ride parking photo plus GPS decides whether a user is charged or fined, and whether a bike is reported stolen.
- **Insurance:** remote claims are assessed from photos, increasingly by automated triage.
- **Public funds:** EU farm subsidies (CAP) accept geotagged photos as evidence; compensation schemes accept geotagged damage photos.
- **Field work and gig platforms:** a photo at the right place releases payment.

**The shift:** location and photos used to *support* a human's judgement. Now they often *are* the judgement.

> 📌 Evidence to find: share of deliveries and claims verified by photo; examples of fully automated claim handling.

## 2. Location is easy to fake

- **Radio spoofing and jamming** once required military equipment; it can now be done with cheap software-defined radios.
- **Fake-GPS apps** are freely available, and photo metadata can be edited in seconds.
- **Interference is no longer rare:** daily around conflict zones, and now regularly reported around the Baltic Sea and the EU's eastern border.
- **Built-in defences don't keep up:** receiver anti-spoofing is proprietary, and spoofing *"evolves like a computer virus"*, outpacing devices built before each new technique.
- **Experts' main advice:** *"Never rely on GNSS as the sole and ONLY source of positioning, navigation and timing information."* Yet almost every app does.

> 📌 Evidence to find: Baltic and Nordic aviation interference reports; cost of spoofing equipment; name of the session speaker for the quotes.

## 3. Images are easy to fake

- **AI generators** produce realistic photos of damage, deliveries or crops in seconds, for free.
- **Real photos get recycled** from other places and dates.
- **Detection tools lag behind** each new generator and return probabilities, not proof.

> 📌 Evidence to find: documented AI-image fraud in insurance claims or deliveries; accuracy limits of AI-image detectors.

## 4. The combined weak spot

**Automated systems check that a proof *exists*, not that it is *true*.** The harm runs in both directions:

| Who | What goes wrong |
| --- | --- |
| **Fraudsters** | Fake a photo or location → payouts, subsidies, "proof" of work never done |
| **Honest people** | Real location spoofed → claims doubted, bikes flagged stolen, fines for "wrong parking" |
| **Critical operations** | GNSS-guided machinery and logistics fail under jamming → delayed harvests and food deliveries |
| **The public** | Fabricated images spread as evidence during crises |

A person may know they are in Poland while every automated system on their phone believes they are in Lima.

## 5. Why now

1. **AI image generation became mainstream** and nearly free.
2. **GNSS interference spread** from war zones into EU member states.
3. **Galileo OSNMA became operational** (July 2025): Europe now has authenticated navigation data. **The tool to close the gap finally exists.**

## 6. Our answer

An independent position check that never trusts GNSS alone:

- **Galileo OSNMA** authenticates the navigation data, something civil GPS cannot do.
- **Cross-checks** against GPS, cellular networks, Wi-Fi, network time and device sensors.
- **Copernicus** Earth observation tells real attacks from normal signal loss and corroborates visible damage.
- **Server-side detection** can be updated as spoofing evolves, and raw evidence is kept so results can be re-examined later.

On top of the trusted position: photos sealed to a verified place and time, which supports damage evidence, proof of delivery and completion, and a defence against AI fakes. It complements C2PA: **C2PA proves a photo wasn't altered; we prove where it was taken.**

We don't make fraud impossible. We make it much harder to get away with, and much easier to prove when something doesn't add up.

---

**One-liner:** *Automated systems trust photos and GPS as proof. AI can fake the photo, spoofing can fake the location. We restore the proof, using Europe's own satellites.*
