import React, { useEffect, useState } from 'react';
import { getExtensionsRegistry, SupersetClient, t } from '@superset-ui/core';
import { Button } from '@superset-ui/core/components';
import { useSelector } from 'react-redux';

type PublicationState = {
  published: boolean;
  dashboardKey?: string;
  productUrl?: string;
};

function NeoRetailPublishButton() {
  const dashboardId = useSelector((state: any) => state.dashboardInfo?.id);
  const userId = useSelector((state: any) => state.dashboardInfo?.userId);
  const [publication, setPublication] = useState<PublicationState>({ published: false });
  const [authorized, setAuthorized] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!dashboardId || !userId) return;
    SupersetClient.get({
      endpoint: `/api/neoretail/dashboard/${dashboardId}/publication`,
    })
      .then(response => {
        setPublication(response.json as PublicationState);
        setAuthorized(true);
      })
      .catch(() => setAuthorized(false));
  }, [dashboardId, userId]);

  if (!dashboardId || !userId || !authorized) return null;

  const publish = async () => {
    setBusy(true);
    setMessage('');
    setError(false);
    try {
      const response = await SupersetClient.post({
        endpoint: `/api/neoretail/dashboard/${dashboardId}/publish`,
        jsonPayload: {},
      });
      const next = response.json as PublicationState & { message?: string };
      setPublication(next);
      setMessage(next.message || t('Dashboard publicado no NeoRetail.'));
    } catch (reason: any) {
      setError(true);
      setMessage(reason?.message || t('Não foi possível publicar no NeoRetail.'));
    } finally {
      setBusy(false);
    }
  };

  return React.createElement(
    'div',
    { style: { display: 'flex', alignItems: 'center', gap: 8 } },
    React.createElement(
      Button,
      {
        buttonStyle: publication.published ? 'secondary' : 'primary',
        buttonSize: 'small',
        loading: busy,
        disabled: busy,
        onClick: publish,
        'data-test': 'publish-neoretail-button',
      },
      publication.published
        ? t('Atualizar no NeoRetail')
        : t('Publicar no NeoRetail'),
    ),
    message
      ? React.createElement(
          'small',
          { style: { color: error ? '#c82639' : '#16865c', whiteSpace: 'nowrap' } },
          message,
        )
      : null,
  );
}

export default function setupExtensions() {
  getExtensionsRegistry().set('dashboard.nav.right', NeoRetailPublishButton);
}
