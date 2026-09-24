import { Nav } from '../components/Nav'
import { Footer } from '../components/Footer'
import { Hero } from '../components/sections/Hero'
import { Why } from '../components/sections/Why'
import { How } from '../components/sections/How'
import { Rules } from '../components/sections/Rules'
import { Session } from '../components/sections/Session'
import { FeatureIndex } from '../components/sections/FeatureIndex'
import { NonGoals } from '../components/sections/NonGoals'
import { Download } from '../components/sections/Download'

// The landing page. The section order is the argument, not a feature list: the window as it
// opens → why a person needs it beside the command → how it reads without scanning a disk →
// who writes and who only reads → handing a line to an agent → the depth pages → what it
// refuses → the installer.
export function Landing() {
  return (
    <>
      <Nav />
      <Hero />
      <Why />
      <How />
      <Rules />
      <Session />
      <FeatureIndex />
      <NonGoals />
      <Download />
      <Footer />
    </>
  )
}
