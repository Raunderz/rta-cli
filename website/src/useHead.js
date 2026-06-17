import { useEffect } from 'preact/hooks';

export function useHead({ title, description } = {}) {
  useEffect(() => {
    const prevTitle = document.title;

    if (title) {
      document.title = `${title} | Rta`;
    }

    if (description) {
      let meta = document.querySelector('meta[name="description"]');
      if (meta) {
        const prevContent = meta.getAttribute('content');
        meta.setAttribute('content', description);
        return () => {
          document.title = prevTitle;
          meta.setAttribute('content', prevContent);
        };
      }
    }

    return () => {
      document.title = prevTitle;
    };
  }, [title, description]);
}
