<!-- 登录页：顶栏固定；仅插画列与表单区随布局切换 -->
<template>
  <div class="login-page-root flex h-screen w-full flex-col overflow-hidden">
    <FaLoginCenterBackdrop v-if="panelAlign === 'center'" viewport-fixed />
    <FaAuthTopBar v-model:panel-align="panelAlign" />

    <div
      class="login-auth-split relative z-1 flex min-h-0 flex-1 overflow-hidden"
      :class="`login-auth-split--${panelAlign}`"
    >
      <div
        v-if="panelAlign !== 'center'"
        class="login-auth-split__col login-auth-split__col--illustration"
      >
        <FaLoginLeftView hide-top-branding />
      </div>

      <div
        class="login-auth-split__col login-auth-split__col--form login-page-panel relative flex min-h-0 min-w-0 flex-col"
        :class="panelAlign === 'center' ? 'bg-transparent' : 'bg-(--el-bg-color-page)'"
      >
        <div
          class="login-page-panel__main relative z-1 flex min-h-0 flex-1 flex-col overflow-hidden px-5 pb-2 pt-14 md:px-10 md:pt-18"
        >
          <ElScrollbar>
            <div
              class="login-page-panel__scroll pb-6"
              :class="panelAlign === 'center' && 'login-page-panel__scroll--centered'"
            >
              <div
                class="login-panel-align-row flex w-full items-center justify-center max-sm:min-h-0"
                :class="
                  panelAlign === 'center'
                    ? 'min-h-0 flex-1 py-4'
                    : 'min-h-[min(720px,calc(100vh-13rem))]'
                "
              >
                <div class="auth-right-wrap">
                  <div class="form">
                    <div class="form-intro">
                      <h3 class="title">{{ panelTitle }}</h3>
                      <p class="sub-title">{{ panelSubTitle }}</p>
                    </div>

                    <FaLoginAccountForm
                      ref="accountFormRef"
                      v-model:is-passing="isPassing"
                      v-model:is-click-pass="isClickPass"
                      v-model:login-form="loginForm"
                      :rules="rules"
                      :captcha-state="captchaState"
                      :code-loading="codeLoading"
                      :demo-account-key="demoAccountKey"
                      :accounts="accounts"
                      :form-key="formKey"
                      :is-dark="isDark"
                      :drag-verify-text-color="dragVerifyTextColor"
                      :loading="loading"
                      @submit="handleSubmit"
                      @setup-account="setupAccount"
                      @get-captcha="getCaptcha"
                    />
                  </div>
                </div>
              </div>
            </div>
          </ElScrollbar>
        </div>

        <footer
          class="login-page-footer login-page-footer--pinned shrink-0 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-3"
          :class="panelAlign === 'center' && 'login-page-footer--floating-layout'"
        >
          <div class="login-footer-text text-sm">
            <div class="login-footer-row">
              <a
                :href="configStore.configData?.git_code?.config_value || '#'"
                target="_blank"
                rel="noopener noreferrer"
                class="login-page-footer__link"
              >
                {{ footerCopyright }}
              </a>
            </div>
            <span class="login-page-footer__sep login-footer-sep-center">|</span>
            <div class="login-footer-row">
              <a
                :href="configStore.configData?.help_doc?.config_value || '#'"
                target="_blank"
                rel="noopener noreferrer"
                class="login-page-footer__link"
              >
                帮助
              </a>
              <span class="login-page-footer__sep">|</span>
              <a
                :href="configStore.configData?.privacy?.config_value || '#'"
                target="_blank"
                rel="noopener noreferrer"
                class="login-page-footer__link"
              >
                隐私
              </a>
              <span class="login-page-footer__sep">|</span>
              <a
                :href="configStore.configData?.clause?.config_value || '#'"
                target="_blank"
                rel="noopener noreferrer"
                class="login-page-footer__link"
              >
                条款
              </a>
              <span
                v-if="configStore.configData?.keep_record?.config_value"
                class="login-page-footer__sep"
                >|</span
              >
              <span
                v-if="configStore.configData?.keep_record?.config_value"
                class="login-page-footer__record"
              >
                {{ configStore.configData.keep_record.config_value }}
              </span>
            </div>
          </div>
        </footer>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { LocationQuery, RouteLocationRaw } from "vue-router";
import AuthAPI, { type CaptchaInfo, type LoginFormData } from "@/api/module_system/auth";
import { useConfigStore, useAppStore, useSettingsStore, useUserStore } from "@stores";
import { HttpError } from "@utils";
import { ElNotification, type FormRules } from "element-plus";
import type { Account, AccountKey } from "./types";
import FaLoginAccountForm from "@/components/views/fa-login/forms/FaLoginAccountForm.vue";
import FaAuthTopBar from "@/components/views/fa-login/widgets/FaAuthTopBar.vue";
import { useLoginPanelAlign } from "@/components/views/fa-login/composables/useLoginPanelAlign";

defineOptions({ name: "Login" });

const configStore = useConfigStore();
const settingStore = useSettingsStore();
const appStore = useAppStore();
const { isDark } = storeToRefs(settingStore);
const { t } = useI18n();

const { panelAlign } = useLoginPanelAlign();

const panelTitle = computed(() => t("login.title"));
const panelSubTitle = computed(() => t("login.subTitle"));
const footerCopyright = "广西创启恒达科技有限公司版权所有";

const dragVerifyTextColor = computed(() =>
  isDark.value ? "rgba(255, 255, 255, 0.45)" : "var(--fa-gray-700)"
);
const formKey = ref(0);

const accounts = computed<Account[]>(() => [
  {
    key: "super",
    label: t("login.roles.super"),
    username: "super",
    password: "123456",
    roles: ["R_SUPER"],
  },
  {
    key: "admin",
    label: t("login.roles.admin"),
    username: "admin",
    password: "123456",
    roles: ["R_ADMIN"],
  },
  {
    key: "user",
    label: t("login.roles.user"),
    username: "user",
    password: "123456",
    roles: ["R_USER"],
  },
]);

const demoAccountKey = ref<AccountKey>("super");
const userStore = useUserStore();
const router = useRouter();
const route = useRoute();
const isPassing = ref(false);
const isClickPass = ref(false);

const accountFormRef = ref<InstanceType<typeof FaLoginAccountForm> | null>(null);

const loading = ref(false);
const codeLoading = ref(false);

const loginForm = reactive<LoginFormData>({
  username: "",
  password: "",
  captcha: "",
  captcha_key: "",
  remember: true,
  login_type: "PC端",
});

const captchaState = reactive<CaptchaInfo>({
  enable: false,
  key: "",
  img_base: "",
});

const rules = computed<FormRules>(() => {
  const base: FormRules = {
    username: [
      {
        required: true,
        trigger: "blur",
        message: t("login.message.username.required"),
      },
    ],
    password: [
      {
        required: true,
        trigger: "blur",
        message: t("login.message.password.required"),
      },
      {
        min: 6,
        message: t("login.message.password.min"),
        trigger: "blur",
      },
    ],
  };
  if (captchaState.enable) {
    base.captcha = [
      {
        required: true,
        trigger: "blur",
        message: t("login.message.captchaCode.required"),
      },
    ];
  }
  return base;
});

function setupAccount(key: AccountKey) {
  const selected = accounts.value.find((a: Account) => a.key === key);
  demoAccountKey.value = key;
  loginForm.username = selected?.username ?? "";
  loginForm.password = selected?.password ?? "";
}

async function getCaptcha() {
  try {
    codeLoading.value = true;
    const response = await AuthAPI.getCaptcha();
    const data = response.data.data;
    loginForm.captcha_key = data.key;
    captchaState.img_base = data.img_base;
    captchaState.enable = data.enable;
  } catch {
    captchaState.enable = false;
    loginForm.captcha = "";
    loginForm.captcha_key = "";
  } finally {
    codeLoading.value = false;
  }
}

function resolveRedirectTarget(query: LocationQuery): RouteLocationRaw {
  const defaultPath = "/";
  const rawRedirect = (query.redirect as string) || defaultPath;
  try {
    const resolved = router.resolve(rawRedirect);
    return {
      path: resolved.path,
      query: resolved.query,
    };
  } catch {
    return { path: defaultPath };
  }
}

onMounted(async () => {
  setupAccount("super");
  await configStore.getConfig(true);
  if (userStore.isLogin) {
    await router.replace(resolveRedirectTarget(route.query));
    return;
  }
  getCaptcha();
});

const handleSubmit = async () => {
  if (!accountFormRef.value) return;

  try {
    const valid = await accountFormRef.value.validate?.();
    if (!valid) return;

    if (!isPassing.value) {
      isClickPass.value = true;
      return;
    }

    loading.value = true;

    await userStore.login(loginForm);
    await router.replace(resolveRedirectTarget(route.query));

    if (settingStore.showGuide) {
      appStore.showGuide(true);
    }
  } catch (error) {
    await getCaptcha();
    if (!(error instanceof HttpError)) {
      console.error("[Login] Unexpected error:", error);
      ElNotification({
        title: "提示",
        message: error instanceof Error ? error.message : String(error),
        type: "error",
      });
    }
  } finally {
    loading.value = false;
    accountFormRef.value?.resetDragVerify?.();
  }
};
</script>

<style scoped lang="scss">
@use "../../../../components/views/fa-login/fa-login";
</style>
