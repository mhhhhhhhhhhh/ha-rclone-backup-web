const allowed = [
  'Die Anmeldesitzung ist abgelaufen. Starte die iCloud-Anmeldung erneut.',
  'Bitte gib einen MFA-Code ein.',
  'Der MFA-Code wurde nicht akzeptiert. Prüfe den Code oder starte die Anmeldung erneut.',
  'Die Anmeldung wurde abgelehnt. Prüfe deine Zugangsdaten.',
  'Der Anmeldeablauf konnte nicht fortgesetzt werden. Starte die Einrichtung erneut.',
  'Die rclone-Anfrage ist fehlgeschlagen. Es werden keine Eingabedaten angezeigt.',
  'address already in use',
];
export function safeRcloneError(value: unknown): string {
  if (typeof value === 'object' && value !== null && 'error' in value) {
    return safeRcloneError((value as {error: unknown}).error);
  }
  if (typeof value === 'string') {
    const exact = allowed.find(message => message === value);
    if (exact) return exact;
    try {
      const parsed: unknown = JSON.parse(value);
      if (typeof parsed === 'object' && parsed !== null) return safeRcloneError(parsed);
    } catch { /* Never return arbitrary input-containing strings. */ }
    if (/^\d{3} (Unauthorized|Forbidden|Bad Gateway|Service Unavailable)$/.test(value)) return value;
  }
  return 'Die rclone-Anfrage ist fehlgeschlagen. Es werden keine Eingabedaten angezeigt.';
}
