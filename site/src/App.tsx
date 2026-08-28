import { useEffect } from "react";
import { componentFor } from "./routes";

// The client shell. There is no router: the page is chosen from the route map by the current
// path, and every link that leaves this page is a plain full load, because each address is a
// static file the prerender already wrote. The same App is what entry-server renders on the
// build side, so the client and the static file agree by construction.
export function App({ path }: { path: string }) {
  useEffect(() => {
    const els = Array.from(document.querySelectorAll<HTMLElement>(".reveal"));
    if (!("IntersectionObserver" in window)) {
      els.forEach((el) => el.classList.add("in"));
      return;
    }
    // This only toggles an element's own opacity class. It never scrolls anything.
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("in");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1 },
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, [path]);

  const Page = componentFor(path);
  return <Page />;
}
