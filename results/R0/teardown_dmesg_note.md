# Nota: dmesg przy teardownie headless (NIE pad GPU) — 2026-08-05

Kontekst: intencjonalny `kill` headless PX4+gz po zaliczeniu A1 (misja PASS 99.9Hz sekundy wczesniej).
Objaw: exit-144 w subshellu + ponizsze wpisy dmesg w momencie killa.

```
[36969.231095] misc dxg: dxgk: dxgkio_query_adapter_info: Ioctl failed: -2
[36969.233206] misc dxg: dxgk: dxgkio_query_adapter_info: Ioctl failed: -2
[36969.234452] misc dxg: dxgk: dxgkio_query_adapter_info: Ioctl failed: -2
[36969.236491] misc dxg: dxgk: dxgkio_query_adapter_info: Ioctl failed: -2
[36969.421816] misc dxg: dxgk: dxgkio_query_adapter_info: Ioctl failed: -2
[36969.513426] misc dxg: dxgk: dxgkio_wait_sync_object_cpu: wait_completion_interruptible: -512
[36969.518001] misc dxg: dxgk: dxgkio_wait_sync_object_cpu: Ioctl failed: -512
[36970.952128] WSL (12168 - CaptureCrash): Capturing crash for pid: 43975, executable: !usr!bin!ruby3.2, signal: 6, port: 50005
```

## Ocena wg A5 (doprecyzowanie PRE §4):
- Sygnatura padu A5 = `dxg ioctl -22`. Tu: `ioctl -2` (ENOENT, query_adapter_info) i `-512` (ERESTARTSYS = syscall PRZERWANY moim sygnalem kill) — NIE -22.
- ruby/gz SIGABRT (sig 6) = abort przy wymuszonym teardownie procesu trzymajacego kontekst GPU, nie spontaniczny crash pod obciazeniem.
- Stack byl stabilny w trakcie pracy (A1: pelna misja, odometria 99.9Hz, /clock 249Hz).
- WERDYKT: **artefakt zarzadzania procesami przy killu, NIE pad GPU**. Nie liczy sie do progu A5.
- Wniosek operacyjny: unikac SIGKILL sim mid-GPU; dla A2 obserwowac exit-144+dxg-22 SPONTANICZNY podczas biegu, nie przy intencjonalnym stopie.
