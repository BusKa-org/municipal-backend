# Infraestrutura OpenStack

## Estrutura
- `versions.tf`: versões mínimas do Terraform e provider.
- `providers.tf`: configuração do provider OpenStack via `cloud_name` definido no `clouds.yaml` local.
- `main.tf`: recursos da VM.
- `variables.tf`: variáveis de entrada.
- `outputs.tf`: saídas úteis (ID, nome e IPv4).
- `terraform.tfvars.example`: exemplo de parametrização.
- `clouds.yaml` (ignorado no git): credenciais do OpenStack.

## Pré-requisitos
- Terraform >= 1.5
- Um `clouds.yaml` válido com a entrada usada em `cloud_name` (padrão `openstack`). Coloque-o em `~/.config/openstack/clouds.yaml` ou mantenha-o no diretório e exporte `OS_CLIENT_CONFIG_FILE=$(pwd)/clouds.yaml`.

## Uso
1. Copie `terraform.tfvars.example` para `terraform.tfvars` e preencha os valores.
2. Opcional: ajuste `cloud_name` para outra entrada do seu `clouds.yaml`.
3. `terraform init`
4. `terraform plan`
5. `terraform apply`

## Boas práticas
- Não commitar `terraform.tfvars`, `clouds.yaml` ou *tfstate*. Já estão no `.gitignore`.