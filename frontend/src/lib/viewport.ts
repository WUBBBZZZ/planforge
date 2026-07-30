import { useEffect, useState } from "react";

const MOBILE_MEDIA_QUERY = "(max-width: 767px)";

export function useNarrowViewport(query = MOBILE_MEDIA_QUERY): boolean {
  const [matches, setMatches] = useState(
    () => typeof window !== "undefined" && window.matchMedia(query).matches,
  );

  useEffect(() => {
    const media = window.matchMedia(query);
    const onChange = () => setMatches(media.matches);
    onChange();
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, [query]);

  return matches;
}
