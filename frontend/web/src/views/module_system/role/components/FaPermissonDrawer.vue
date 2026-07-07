<!-- 角色授权 -->
<template>
  <FaDrawer
    v-model="drawerVisible"
    :title="'【' + props.roleName + '】权限分配'"
    :size="drawerSize"
    destroy-on-close
    @close="handleCancel"
  >
    <div class="drawer-perm-content flex flex-col flex-1 overflow-hidden">
      <ElMain class="h-full min-h-0">
        <div class="flex gap-[10px]">
          <div class="w-[10px] bg-(--el-color-primary)"></div>
          <div>
            <span class="text-[16px]">菜单授权</span>
            <ElTooltip placement="right">
              <template #content>
                <span>勾选菜单和对应的功能按钮权限</span>
              </template>
              <ElIcon class="ml-1 inline-block cursor-pointer">
                <QuestionFilled />
              </ElIcon>
            </ElTooltip>
            <div class="mt-2 text-[12px] text-[var(--el-text-color-secondary)]">
              单组织模式下默认使用全部数据权限，不再单独配置部门数据范围。
            </div>
          </div>
        </div>
        <div class="mt-3 flex-1 min-h-0">
          <FaMenuTreeTable
            ref="menuTreeTableRef"
            :menu-tree="rawMenuTree"
            :checked-ids="menuCheckedIds"
            :loading="loading"
          />
        </div>
      </ElMain>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <ElButton @click="handleCancel">取 消</ElButton>
        <ElButton type="primary" :loading="loading" @click.stop="handleDrawerSave">确 定</ElButton>
      </div>
    </template>
  </FaDrawer>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from "vue";
import { QuestionFilled } from "@element-plus/icons-vue";
import FaMenuTreeTable from "@/components/others/fa-menu-tree-table/index.vue";
import RoleAPI, { permissionDataType } from "@/api/module_system/role";
import MenuAPI, { MenuTable } from "@/api/module_platform/menu";
import { DeviceEnum } from "@/enums/settings/device.enum";
import { useUserStore, useAppStore } from "@stores";
import { ElMessage } from "element-plus";

const props = defineProps<{
  roleName: string;
  roleId: number;
  modelValue: boolean;
}>();

interface Emits {
  "update:modelValue": [v: boolean];
  saved: [];
}

const emit = defineEmits<Emits>();

const appStore = useAppStore();
const drawerSize = computed(() => (appStore.device === DeviceEnum.DESKTOP ? "740px" : "90%"));

const drawerVisible = computed({
  get: () => props.modelValue,
  set(v) {
    emit("update:modelValue", v);
  },
});

const loading = ref(false);
const rawMenuTree = ref<MenuTable[]>([]);
const menuCheckedIds = ref<number[]>([]);
const menuTreeTableRef = ref<InstanceType<typeof FaMenuTreeTable>>();

const HIDDEN_MENU_PERMISSION_PREFIXES = [
  "module_system:dept:",
  "module_system:position:",
  "module_system:tenant:",
  "module_package:package:",
] as const;

const HIDDEN_MENU_ROUTE_PATHS = new Set([
  "/system/dept",
  "/system/position",
  "/platform/tenant",
  "/platform/package",
]);

const HIDDEN_MENU_COMPONENT_PATHS = new Set([
  "/module_system/dept/index",
  "/module_system/position/index",
  "/module_platform/tenant/index",
  "/module_platform/package/index",
]);

const HIDDEN_MENU_TITLES = new Set(["部门管理", "岗位管理", "租户管理", "套餐管理"]);

function normalizeMatchPath(value?: string): string {
  const trimmed = (value ?? "").trim();
  if (!trimmed) return "";
  const normalized = trimmed.replace(/\/+/g, "/").replace(/\/$/, "");
  return normalized.startsWith("/") ? normalized : `/${normalized}`;
}

function matchesBlockedPath(path: string, blockedPaths: Set<string>): boolean {
  if (!path) return false;
  if (blockedPaths.has(path)) return true;
  return Array.from(blockedPaths).some((blocked) => path.startsWith(`${blocked}/`));
}

function shouldHideBusinessMenu(item: MenuTable): boolean {
  const permission = (item.permission ?? "").trim();
  if (HIDDEN_MENU_PERMISSION_PREFIXES.some((prefix) => permission.startsWith(prefix))) {
    return true;
  }

  if (matchesBlockedPath(normalizeMatchPath(item.route_path), HIDDEN_MENU_ROUTE_PATHS)) {
    return true;
  }

  if (
    matchesBlockedPath(normalizeMatchPath(item.component_path), HIDDEN_MENU_COMPONENT_PATHS)
  ) {
    return true;
  }

  return HIDDEN_MENU_TITLES.has((item.title ?? "").trim());
}

function filterHiddenBusinessMenus(items: MenuTable[]): MenuTable[] {
  return items.reduce<MenuTable[]>((acc, item) => {
    if (shouldHideBusinessMenu(item)) {
      return acc;
    }

    const children = item.children?.length ? filterHiddenBusinessMenus(item.children) : item.children;
    acc.push({
      ...item,
      children,
    });
    return acc;
  }, []);
}

const permissionState = ref<permissionDataType>({
  role_ids: [],
  menu_ids: [],
  data_scope: 4,
  dept_ids: [],
});

const init = async () => {
  loading.value = true;
  try {
    const menuResponse = await MenuAPI.listMenu();
    rawMenuTree.value = filterHiddenBusinessMenus(menuResponse.data.data || []);

    const roleResponse = await RoleAPI.detailRole(props.roleId);
    const savedMenuIds = roleResponse.data.data.menus?.map((menu: any) => menu.id) || [];

    permissionState.value = {
      role_ids: [props.roleId],
      menu_ids: savedMenuIds,
      data_scope: 4,
      dept_ids: [],
    };

    menuCheckedIds.value = savedMenuIds;
  } catch (error: unknown) {
    const msg = error instanceof Error ? error.message : String(error);
    ElMessage.error("获取权限数据失败: " + msg);
  } finally {
    loading.value = false;
  }
};

function handleCancel() {
  drawerVisible.value = false;
}

async function handleDrawerSave() {
  try {
    if (props.roleId === 1) {
      ElMessage.warning("系统默认角色，不可操作");
      return;
    }
    loading.value = true;

    const checkedIds = menuTreeTableRef.value?.getCheckedIds() ?? [];
    const menu_ids = expandMenuIdsWithAncestors(checkedIds, rawMenuTree.value);

    const submitData: permissionDataType = {
      role_ids: [props.roleId],
      menu_ids,
      data_scope: 4,
      dept_ids: [],
    };

    await RoleAPI.setPermission(submitData);

    const userStore = useUserStore();
    await userStore.getUserInfo();

    drawerVisible.value = false;
    emit("saved");
  } catch (error: unknown) {
    console.error(error);
  } finally {
    loading.value = false;
  }
}

/** 将选中的菜单/按钮 ID 展开为包含所有祖先菜单的完整集合 */
function expandMenuIdsWithAncestors(checkedIds: number[], roots: MenuTable[]): number[] {
  const parentById = new Map<number, number | undefined>();
  const walk = (nodes: MenuTable[], parent: number | undefined) => {
    for (const n of nodes) {
      const id = n.id!;
      parentById.set(id, parent);
      if (n.children?.length) walk(n.children as MenuTable[], id);
    }
  };
  walk(roots, undefined);
  const out = new Set<number>();
  for (const id of checkedIds) {
    let cur: number | undefined = id;
    while (cur !== undefined) {
      out.add(cur);
      cur = parentById.get(cur);
    }
  }
  return [...out];
}

onMounted(async () => {
  await init();
});
</script>
