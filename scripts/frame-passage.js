import { mountCinematicFilm } from '@base/cinematic-film';
import { film } from '../shared/film.mjs';
import { mountFilmSurface } from '@base/film-surface';

export function mount({element}) {
  const grain=element.closest('[data-gazette-component]')?.querySelector('.cinematic-grain');
  const texture=document.getElementById('cinematic-material')?.content.firstElementChild?.cloneNode(true);
  if(grain&&texture)grain.append(texture);
  const disposeFilm=mountCinematicFilm({element,film});
  const disposeSurface=mountFilmSurface({element});
  return ()=>{disposeSurface?.();disposeFilm?.();texture?.remove();};
}
