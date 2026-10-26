export type Question = {
  Name?: string; Help?: string; Default?: unknown; Required?: boolean;
  IsPassword?: boolean; Type?: string; Exclusive?: boolean;
  Examples?: Array<{Value: string; Help?: string}>;
};
export type ConfigStep = { State?: string; Option?: Question | null; Error?: string };
export type RcCall = (path: string, body: Record<string, unknown>) => Promise<ConfigStep>;
export type Ask = (question: Question, error?: string) => Promise<string | null>;
export class SetupError extends Error {
  readonly code: string;
  constructor(message: string, code = 'REQUEST_FAILED') { super(message); this.code = code; }
}

export async function runICloudConfiguration(
  call: RcCall, ask: Ask, name: string,
  parameters: Record<string, unknown>, existing = false,
): Promise<void> {
  // Initial password fields are explicitly obscured before saving by rclone.
  // Do not resend the password or stale cookies in the continuation calls.
  const clean = {...parameters};
  delete clean.cookies; delete clean.trust_token; delete clean._auth_session;
  let step = await call(existing ? '/config/update' : '/config/create', {
    name, ...(existing ? {} : {type: 'iclouddrive'}), parameters: clean,
    opt: {nonInteractive: true, obscure: true},
  });
  let attempts = 0;
  let lastError = '';
  for (let steps = 0; steps < 24; steps++) {
    if (!step.State) {
      if (step.Error) throw new SetupError(step.Error);
      return;
    }
    const question = step.Option;
    if (!question) throw new SetupError('Der Server hat keinen gültigen nächsten Anmeldeschritt geliefert.');
    const result = await ask(question, lastError || step.Error || '');
    if (result === null) throw new SetupError('Einrichtung abgebrochen. Das unvollständige Remote wurde nicht gelöscht.', 'CANCELLED');
    const isCode = /2fa/.test(question.Name || '') && !question.Exclusive;
    if (isCode && !(/^\d{6}$/.test(result) || (question.Name === 'config_2fa' && result.toLowerCase() === 'sms'))) {
      lastError = 'Bitte gib den sechsstelligen Code ein. Für einen SMS-Code ist im ersten MFA-Schritt auch „sms“ möglich.';
      continue;
    }
    if (question.Required && !result) {
      lastError = 'Dieses Feld darf nicht leer sein.';
      continue;
    }
    try {
      step = await call('/config/update', {
        name, parameters: {},
        opt: {nonInteractive: true, continue: true, state: step.State, result},
      });
      attempts = 0; lastError = '';
    } catch (error) {
      if (error instanceof SetupError && error.code === 'MFA_INVALID' && attempts++ < 2) {
        lastError = error.message;
        continue; // Keep the exact state received from rclone, never invent a state.
      }
      throw error;
    }
  }
  throw new SetupError('Zu viele Anmeldeschritte. Starte die Einrichtung erneut.');
}
