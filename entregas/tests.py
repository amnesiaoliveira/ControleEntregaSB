from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Entrega, EventoEntrega, MotivoInsucesso, Motorista, Rota


class EntregaFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="operador", password="teste12345")
        self.client.login(username="operador", password="teste12345")
        self.entrega = Entrega.objects.create(
            cliente="Maria Silva",
            rua="Rua das Flores",
            numero="123",
            bairro="Centro",
            ponto_referencia="Próximo à praça",
            volumes=4,
            pdv="02",
            operador="Ana",
            motorista="Carlos",
        )

    def test_controle_lista_entregas(self):
        response = self.client.get(reverse("entregas:controle"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.entrega.numero_controle)
        self.assertContains(response, "Maria Silva")

    def test_cria_entrega(self):
        response = self.client.post(
            reverse("entregas:criar"),
            {
                "cliente": "João Pereira",
                "rua": "Avenida Brasil",
                "numero": "45",
                "bairro": "Jardim",
                "ponto_referencia": "",
                "volumes": 2,
                "pdv": "04",
                "data_prevista": timezone.localdate(),
                "operador": "Rita",
                "motorista": "Marcos",
                "status": Entrega.Status.PENDENTE,
                "observacoes": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        entrega = Entrega.objects.get(cliente="João Pereira")
        self.assertEqual(entrega.sequencia_controle, 2)
        self.assertEqual(entrega.numero_controle, f"{timezone.localdate():%Y%m%d}-002")

    def test_controle_reinicia_a_contagem_por_dia(self):
        ontem = timezone.localdate() - timedelta(days=1)
        entrega_ontem = Entrega.objects.create(
            data_controle=ontem,
            cliente="Cliente de ontem",
            rua="Rua Antiga",
            numero="10",
            bairro="Centro",
            volumes=1,
            pdv="01",
            operador="Ana",
            motorista="Carlos",
        )

        self.assertEqual(entrega_ontem.sequencia_controle, 1)
        self.assertEqual(entrega_ontem.numero_controle, f"{ontem:%Y%m%d}-001")

    def test_atualiza_status(self):
        response = self.client.post(
            reverse("entregas:status", args=[self.entrega.pk, Entrega.Status.EM_ROTA])
        )

        self.assertEqual(response.status_code, 302)
        self.entrega.refresh_from_db()
        self.assertEqual(self.entrega.status, Entrega.Status.EM_ROTA)

    def test_relatorio_filtra_por_motorista(self):
        Entrega.objects.create(
            cliente="Cliente B",
            rua="Rua B",
            numero="10",
            bairro="Norte",
            volumes=1,
            pdv="01",
            operador="Ana",
            motorista="Lucia",
        )

        response = self.client.get(reverse("entregas:relatorio"), {"motorista": "Carlos"})

        self.assertContains(response, self.entrega.numero_controle)
        self.assertNotContains(response, "Cliente B")

    def test_cria_rota_com_entregas_pendentes(self):
        outra_entrega = Entrega.objects.create(
            cliente="Cliente rota",
            rua="Rua da Rota",
            numero="50",
            bairro="Centro",
            volumes=3,
            pdv="03",
            operador="Ana",
            motorista="Carlos",
        )

        response = self.client.post(
            reverse("entregas:rota_criar"),
            {
                "motorista": "Carlos",
                "responsavel_saida": "Paulo",
                "observacoes_saida": "Conferido na expedição",
                "entregas": [self.entrega.id, outra_entrega.id],
            },
        )

        self.assertEqual(response.status_code, 302)
        rota = Rota.objects.get(motorista="Carlos")
        self.assertEqual(rota.numero_rota, f"R{timezone.localdate():%Y%m%d}-001")
        self.entrega.refresh_from_db()
        outra_entrega.refresh_from_db()
        self.assertEqual(self.entrega.rota, rota)
        self.assertEqual(self.entrega.status, Entrega.Status.EM_ROTA)
        self.assertEqual(outra_entrega.status, Entrega.Status.EM_ROTA)

    def test_retorno_finaliza_rota_quando_todas_entregas_fecham(self):
        rota = Rota.objects.create(motorista="Carlos")
        self.entrega.rota = rota
        self.entrega.status = Entrega.Status.EM_ROTA
        self.entrega.save(update_fields=["rota", "status"])

        response = self.client.post(
            reverse("entregas:rota_retorno", args=[rota.pk]),
            {
                "observacoes_retorno": "Entrega confirmada",
                "entregas": [self.entrega.id],
                "status": Entrega.Status.ENTREGUE,
                "recebedor_nome": "Maria Silva",
                "recebedor_documento": "123",
                "comprovante_observacao": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.entrega.refresh_from_db()
        rota.refresh_from_db()
        self.assertEqual(self.entrega.status, Entrega.Status.ENTREGUE)
        self.assertEqual(rota.status, Rota.Status.FINALIZADA)

    def test_dashboard_exige_login(self):
        self.client.logout()
        response = self.client.get(reverse("entregas:dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/contas/login/", response["Location"])

    def test_dashboard_renderiza_logado(self):
        response = self.client.get(reverse("entregas:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard de entregas")

    def test_cadastra_motorista(self):
        response = self.client.post(
            reverse("entregas:cadastros"),
            {
                "tipo": "motorista",
                "motorista-nome": "Carlos Silva",
                "motorista-telefone": "9999-0000",
                "motorista-ativo": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Motorista.objects.filter(nome="Carlos Silva").exists())

    def test_cadastros_renderiza(self):
        response = self.client.get(reverse("entregas:cadastros"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cadastros")

    def test_fecha_entrega_com_motivo_e_reagendamento(self):
        motivo, _ = MotivoInsucesso.objects.get_or_create(descricao="Cliente ausente")
        nova_data = timezone.localdate() + timedelta(days=1)

        response = self.client.post(
            reverse("entregas:fechar_entrega", args=[self.entrega.pk]),
            {
                "status": Entrega.Status.REAGENDADA,
                "motivo_insucesso": motivo.pk,
                "reagendada_para": nova_data,
                "recebedor_nome": "",
                "recebedor_documento": "",
                "comprovante_observacao": "Cliente pediu nova tentativa.",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.entrega.refresh_from_db()
        self.assertEqual(self.entrega.status, Entrega.Status.REAGENDADA)
        self.assertEqual(self.entrega.data_prevista, nova_data)
        self.assertTrue(EventoEntrega.objects.filter(entrega=self.entrega).exists())

    def test_relatorio_exporta_csv(self):
        response = self.client.get(reverse("entregas:relatorio"), {"export": "csv"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertContains(response, self.entrega.numero_controle)

    def test_impressao_romaneio_renderiza(self):
        rota = Rota.objects.create(motorista="Carlos")
        self.entrega.rota = rota
        self.entrega.status = Entrega.Status.EM_ROTA
        self.entrega.save(update_fields=["rota", "status"])

        response = self.client.get(reverse("entregas:rota_imprimir", args=[rota.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Romaneio de entrega")
