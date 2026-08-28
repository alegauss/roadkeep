import { Nav } from "../components/Nav";
import { Footer } from "../components/Footer";
import { MarkSprite } from "../components/ui/Mark";
import { Ad } from "../components/ui/Ad";
import { Hero } from "../components/sections/Hero";
import { Why } from "../components/sections/Why";
import { Mechanism } from "../components/sections/Mechanism";
import { Surfaces } from "../components/sections/Surfaces";
import { Strengths } from "../components/sections/Strengths";
import { Compare } from "../components/sections/Compare";
import { HowItWorks } from "../components/sections/HowItWorks";
import { Decisions } from "../components/sections/Decisions";
import { Evidence } from "../components/sections/Evidence";
import { Install } from "../components/sections/Install";
import { Laws } from "../components/sections/Laws";
import { Proof } from "../components/sections/Proof";
import { Closing } from "../components/sections/Closing";

// The one page. The section order is the argument and not a feature list: what a turn pays
// without this, how a line rots, where the plugin sits, what gets cheaper, what this is not,
// the four calls, where a decision goes, the measurements it started from, how to install it,
// what it refuses to become, and the proof.
//
// The evidence comes *after* the mechanism rather than opening the page, because three numbers
// from somebody else's repository are only an argument once a reader knows what was being
// measured.
//
// Two ad slots, and both sit on a seam the argument had already finished. The strip is under
// the ledger, where the page's first claim has landed; the leaderboard is between the decision
// section and the evidence, far enough from the install block and the closing call that it is
// never the second button on screen.
export function Landing() {
  return (
    <>
      <MarkSprite />
      <Nav />
      <Hero />
      <Why />
      <Ad slot="after-why" format="strip" />
      <Mechanism />
      <Surfaces />
      <Strengths />
      <Compare />
      <HowItWorks />
      <Decisions />
      <Ad slot="mid-page" format="footer" className="mid" />
      <Evidence />
      <Install />
      <Laws />
      <Proof />
      <Closing />
      <Footer />
    </>
  );
}
