/* The links remain usable anchors and all guides stay visible without JavaScript. */
(() => {
  const container = document.querySelector('[data-install-tabs]');
  if (!container) return;
  const tablist = container.querySelector('.platform-tabs');
  const tabs = Array.from(tablist.querySelectorAll('a'));
  const panels = tabs.map(tab => document.getElementById(tab.hash.slice(1)));
  if (panels.some(panel => !panel)) return;

  tablist.setAttribute('role', 'tablist');
  tabs.forEach((tab, index) => {
    tab.setAttribute('role', 'tab');
    tab.setAttribute('aria-controls', panels[index].id);
    panels[index].setAttribute('role', 'tabpanel');
    panels[index].setAttribute('aria-labelledby', tab.id);
    panels[index].tabIndex = 0;
  });

  const select = (index, updateUrl = false) => {
    tabs.forEach((tab, position) => {
      const active = position === index;
      tab.setAttribute('aria-selected', String(active));
      tab.tabIndex = active ? 0 : -1;
      panels[position].hidden = !active;
    });
    if (updateUrl) history.replaceState(null, '', tabs[index].hash);
  };

  const indexFromHash = () => {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); }
    catch { return -1; }
    const target = document.getElementById(id);
    return panels.findIndex(panel => target && panel.contains(target));
  };

  tabs.forEach((tab, index) => {
    tab.addEventListener('click', event => {
      // Preserve opening an OS guide in a new tab with modified clicks.
      if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      select(index, true);
    });
    tab.addEventListener('keydown', event => {
      let next;
      if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      else if (event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
      else if (event.key === 'Home') next = 0;
      else if (event.key === 'End') next = tabs.length - 1;
      else if (event.key === ' ') next = index;
      else return;
      event.preventDefault();
      select(next, true);
      tabs[next].focus();
    });
  });

  const revealHash = () => {
    const index = indexFromHash();
    if (index < 0) return false;
    select(index);
    const target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
    (target === panels[index] ? tablist : target).scrollIntoView();
    return true;
  };
  // Select the OS family only; customers choose their Mac chip themselves.
  const platform = navigator.userAgentData?.platform || navigator.platform || '';
  const defaultId = /mac/i.test(platform) ? 'macos' : /linux/i.test(platform) ? 'linux' : 'windows';
  select(panels.findIndex(panel => panel.id === defaultId));
  revealHash();
  window.addEventListener('hashchange', revealHash);
})();
