<template>
  <div class="space-y-6">
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
      <!-- Create Fund (when no fund exists) -->
      <template v-if="!currentFund">
        <div class="mb-6">
          <h2 class="text-2xl font-bold text-gray-900">Set Up Wallet</h2>
          <p class="text-sm text-gray-600 mt-2">
            Create a view-only fund by providing your Monero wallet address and
            private view key.
            <strong>Your spend key is never required or stored.</strong>
          </p>
        </div>

        <form @submit.prevent="handleCreateFund" class="space-y-6">
          <div>
            <label
              for="label"
              class="block text-sm font-medium text-gray-700 mb-1"
            >
              Fund Label
            </label>
            <input
              id="label"
              v-model="createForm.label"
              type="text"
              required
              placeholder="e.g. CCS Campaign #123"
              class="w-full px-4 h-9 border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
            />
          </div>

          <div>
            <label
              for="description"
              class="block text-sm font-medium text-gray-700 mb-1"
            >
              Description
              <span class="text-gray-400">optional</span>
            </label>
            <textarea
              id="description"
              v-model="createForm.description"
              rows="3"
              maxlength="2048"
              placeholder="Describe the purpose of this fund..."
              class="w-full px-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange text-sm resize-y"
            ></textarea>
            <p class="text-xs text-gray-500 mt-1">
              Optional description shown in the public widget to help donors
              understand the fund's purpose.
            </p>
          </div>

          <div>
            <label
              for="address"
              class="block text-sm font-medium text-gray-700 mb-1"
            >
              Primary Address
              <span class="text-gray-400">(95 characters)</span>
            </label>
            <input
              id="address"
              v-model="createForm.primary_address"
              type="text"
              required
              placeholder="4AdUndXHHZ9cf2bqQ3P7CF2F9xK2s5f2RMZZU6L5HraAB3Z2TL65E6R4E6T1GtGcY3UphTB2C5sZfrYj7Y52bHvMFbS4fQ"
              maxlength="95"
              class="w-full px-4 h-9 border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange font-mono text-sm"
            />
            <p class="text-xs text-gray-500 mt-1">
              Your Monero primary address, starting with 4, 8, A, or B.
            </p>
          </div>

          <div>
            <label
              for="deposit-address"
              class="block text-sm font-medium text-gray-700 mb-1"
            >
              Deposit Address
              <span class="text-gray-400">optional</span>
            </label>
            <input
              id="deposit-address"
              v-model="createForm.deposit_address"
              type="text"
              placeholder="Defaults to primary address"
              maxlength="95"
              class="w-full px-4 h-9 border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange font-mono text-sm"
            />
            <p class="text-xs text-gray-500 mt-1">
              A separate address for receiving donations. If not specified, the
              primary address is used.
            </p>
          </div>

          <div>
            <label
              for="viewkey"
              class="block text-sm font-medium text-gray-700 mb-1"
            >
              Private View Key
              <span class="text-gray-400">(64 hex characters)</span>
            </label>
            <div class="relative">
              <input
                id="viewkey"
                v-model="createForm.view_key"
                :type="showViewKey ? 'text' : 'password'"
                required
                placeholder="abcdef1234567890..."
                maxlength="64"
                class="w-full px-4 h-9 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange font-mono text-sm"
              />
              <button
                type="button"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                @click="showViewKey = !showViewKey"
              >
                <Eye v-if="!showViewKey" :size="16" />
                <EyeOff v-else :size="16" />
              </button>
            </div>
            <p class="text-xs text-gray-500 mt-1">
              This key allows reading incoming transactions. It does
              <strong>not</strong> allow spending.
            </p>
          </div>

          <div>
            <label
              for="height"
              class="block text-sm font-medium text-gray-700 mb-1"
            >
              Start Height
            </label>
            <input
              id="height"
              v-model.number="createForm.start_height"
              type="number"
              required
              min="0"
              placeholder="e.g. 3280000"
              class="w-full px-4 h-9 border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
            />
            <p class="text-xs text-gray-500 mt-1">
              The block height from which to start scanning. Use 0 for full
              history, or a recent height to scan only new blocks.
            </p>
          </div>

          <div>
            <label
              for="target-amount"
              class="block text-sm font-medium text-gray-700 mb-1"
            >
              Target Amount (XMR)
              <span class="text-gray-400">optional</span>
            </label>
            <input
              id="target-amount"
              v-model="createForm.target_amount_xmr"
              type="text"
              placeholder="e.g. 1000"
              class="w-full px-4 h-9 border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
            />
            <p class="text-xs text-gray-500 mt-1">
              Optional fundraising goal. Displayed on the dashboard and public
              widget.
            </p>
          </div>

          <div
            v-if="createError"
            class="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-2"
          >
            <AlertCircle :size="16" class="text-red-600 flex-shrink-0 mt-0.5" />
            <p class="text-sm text-red-800">{{ createError }}</p>
          </div>

          <Button type="submit" variant="default" :disabled="creating">
            <div class="flex items-center space-x-2">
              <Loader2 v-if="creating" :size="16" class="animate-spin" />
              <PlusCircle v-else :size="16" />
              <span>{{ creating ? "Creating wallet..." : "Create Fund" }}</span>
            </div>
          </Button>
        </form>
      </template>

      <!-- Fund Management (when fund exists) -->
      <template v-else>
        <h2 class="text-2xl font-bold text-gray-900 mb-6">Settings</h2>

        <div class="space-y-8">
          <!-- API Key Section -->
          <div>
            <h3 class="text-lg font-semibold text-gray-900 mb-2">API Key</h3>
            <p class="text-sm text-gray-600 mb-3">
              Your API key is stored locally in the browser. Clear it to
              disconnect and require re-authentication.
            </p>
            <div class="flex gap-3 items-center">
              <input
                :value="maskedKey"
                type="text"
                disabled
                class="flex-1 px-4 h-9 border border-gray-300 rounded-lg bg-gray-50 text-gray-500 font-mono text-sm"
              />
              <Button variant="destructive" @click="handleLogout">
                <div class="flex items-center space-x-1">
                  <LogOut :size="14" />
                  <span>Disconnect</span>
                </div>
              </Button>
            </div>
          </div>

          <!-- Date and Time Format Section -->
          <div>
            <h3 class="text-lg font-semibold text-gray-900 mb-2">
              Date and Time Format
            </h3>
            <p class="text-sm text-gray-600 mb-3">
              This setting affects how dates and times are displayed on the
              dashboard and in all PDF/XML reports.
            </p>
            <div class="mb-3 space-y-1.5">
              <p class="text-xs text-gray-500">Example patterns:</p>
              <div
                v-for="example in formatExamples"
                :key="example.pattern"
                class="flex items-center gap-2 text-xs"
              >
                <code
                  class="bg-gray-100 px-2 py-0.5 rounded font-mono text-gray-700"
                  >{{ example.pattern }}</code
                >
                <span class="text-gray-400">→</span>
                <span class="text-gray-600">{{ example.output }}</span>
              </div>
            </div>
            <div>
              <label
                for="datetime-format"
                class="block text-sm font-medium text-gray-700 mb-1"
              >
                Format pattern
              </label>
              <div class="flex gap-3 items-start">
                <div class="flex-1">
                  <input
                    id="datetime-format"
                    v-model="datetimeFormat"
                    type="text"
                    placeholder="YYYY-MM-DD HH:mm:ss"
                    class="w-full px-4 h-9 border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange font-mono text-sm"
                    @keydown.enter="updateDatetimeFormat"
                  />
                  <p v-if="formatError" class="mt-1.5 text-sm text-red-600">
                    {{ formatError }}
                  </p>
                </div>
                <Button
                  variant="outline"
                  :disabled="savingFormat"
                  @click="updateDatetimeFormat"
                >
                  <div class="flex items-center space-x-1">
                    <Loader2
                      v-if="savingFormat"
                      :size="14"
                      class="animate-spin"
                    />
                    <Save v-else :size="14" />
                    <span>{{ savingFormat ? "Saving..." : "Update" }}</span>
                  </div>
                </Button>
              </div>
            </div>
          </div>

          <!-- Fund Management -->
          <div>
            <h3 class="text-lg font-semibold text-gray-900 mb-2">
              Fund Management
            </h3>

            <div class="space-y-4">
              <div>
                <label
                  for="fund-label"
                  class="block text-sm font-medium text-gray-700 mb-1"
                >
                  Label
                </label>
                <div class="flex gap-3">
                  <input
                    id="fund-label"
                    v-model="newLabel"
                    type="text"
                    class="flex-1 px-4 h-9 border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
                  />
                  <Button
                    variant="outline"
                    :disabled="savingLabel"
                    @click="updateLabel"
                  >
                    <div class="flex items-center space-x-1">
                      <Loader2
                        v-if="savingLabel"
                        :size="14"
                        class="animate-spin"
                      />
                      <Save v-else :size="14" />
                      <span>{{ savingLabel ? "Saving..." : "Update" }}</span>
                    </div>
                  </Button>
                </div>
              </div>

              <div>
                <label
                  for="fund-description"
                  class="block text-sm font-medium text-gray-700 mb-1"
                >
                  Description
                  <span class="text-gray-400">optional</span>
                </label>
                <div class="flex gap-3 items-start">
                  <div class="flex-1">
                    <textarea
                      id="fund-description"
                      v-model="newDescription"
                      rows="3"
                      maxlength="2048"
                      class="w-full px-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange text-sm resize-y"
                    ></textarea>
                  </div>
                  <Button
                    variant="outline"
                    :disabled="savingDescription"
                    @click="updateDescription"
                  >
                    <div class="flex items-center space-x-1">
                      <Loader2
                        v-if="savingDescription"
                        :size="14"
                        class="animate-spin"
                      />
                      <Save v-else :size="14" />
                      <span>{{
                        savingDescription ? "Saving..." : "Update"
                      }}</span>
                    </div>
                  </Button>
                </div>
              </div>

              <div>
                <label
                  for="target-xmr"
                  class="block text-sm font-medium text-gray-700 mb-1"
                >
                  Target Amount (XMR)
                </label>
                <div class="flex gap-3">
                  <input
                    id="target-xmr"
                    v-model="newTargetAmount"
                    type="text"
                    placeholder="e.g. 1000"
                    class="flex-1 px-4 h-9 border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
                  />
                  <Button
                    variant="outline"
                    :disabled="savingTarget"
                    @click="updateTargetAmount"
                  >
                    <div class="flex items-center space-x-1">
                      <Loader2
                        v-if="savingTarget"
                        :size="14"
                        class="animate-spin"
                      />
                      <Save v-else :size="14" />
                      <span>{{ savingTarget ? "Saving..." : "Update" }}</span>
                    </div>
                  </Button>
                </div>
                <p v-if="targetError" class="mt-1.5 text-sm text-red-600">
                  {{ targetError }}
                </p>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1"
                  >Status</label
                >
                <div class="flex gap-3 items-center">
                  <span
                    :class="
                      currentFund.is_active
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    "
                    class="inline-flex items-center px-3 py-1 text-sm font-medium rounded-full"
                  >
                    <CircleCheck
                      v-if="currentFund.is_active"
                      :size="14"
                      class="mr-1"
                    />
                    <CircleX v-else :size="14" class="mr-1" />
                    {{ currentFund.is_active ? "Active" : "Inactive" }}
                  </span>
                  <Button
                    :variant="currentFund.is_active ? 'destructive' : 'default'"
                    size="sm"
                    :disabled="togglingActive"
                    @click="toggleActive"
                  >
                    {{
                      togglingActive
                        ? "Updating..."
                        : currentFund.is_active
                          ? "Deactivate"
                          : "Activate"
                    }}
                  </Button>
                </div>
              </div>

              <div class="mt-4 p-4 bg-gray-50 rounded-lg">
                <h4
                  class="text-sm font-medium text-gray-700 mb-2 flex items-center space-x-1"
                >
                  <Info :size="14" />
                  <span>Fund Details</span>
                </h4>
                <div class="grid grid-cols-2 gap-2 text-sm">
                  <span class="text-gray-500">Fund ID:</span>
                  <span class="font-mono text-gray-700 text-xs">{{
                    currentFund.id
                  }}</span>
                  <span class="text-gray-500">Public UUID:</span>
                  <span class="font-mono text-gray-700 text-xs">{{
                    currentFund.public_uuid
                  }}</span>
                  <span class="text-gray-500">Address:</span>
                  <span class="font-mono text-gray-700 text-xs truncate">{{
                    currentFund.primary_address
                  }}</span>
                  <template
                    v-if="
                      currentFund.deposit_address &&
                      currentFund.deposit_address !==
                        currentFund.primary_address
                    "
                  >
                    <span class="text-gray-500">Deposit Address:</span>
                    <span class="font-mono text-gray-700 text-xs truncate">{{
                      currentFund.deposit_address
                    }}</span>
                  </template>
                  <template v-if="currentFund.description">
                    <span class="text-gray-500">Description:</span>
                    <span class="text-gray-700 text-xs">{{
                      currentFund.description
                    }}</span>
                  </template>
                  <span class="text-gray-500">Start Height:</span>
                  <span class="text-gray-700">{{
                    currentFund.start_height
                  }}</span>
                  <span class="text-gray-500">Created:</span>
                  <span class="text-gray-700">{{
                    formatDate(currentFund.created_at)
                  }}</span>
                </div>
              </div>

              <div class="pt-4 border-t border-gray-200">
                <h4
                  class="text-sm font-semibold text-red-600 mb-2 flex items-center space-x-1"
                >
                  <AlertTriangle :size="14" />
                  <span>Danger Zone</span>
                </h4>
                <p class="text-xs text-gray-500 mb-3">
                  Deleting a fund will remove all associated transaction data.
                  This cannot be undone.
                </p>
                <Button variant="destructive" @click="showDeleteModal = true">
                  <div class="flex items-center space-x-1">
                    <Trash2 :size="14" />
                    <span>Delete Fund</span>
                  </div>
                </Button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Delete Confirmation Modal -->
    <Teleport to="body">
      <div
        v-if="showDeleteModal"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        @click.self="showDeleteModal = false"
      >
        <div class="bg-white rounded-xl p-6 max-w-md mx-4 shadow-xl">
          <div class="flex items-center space-x-2 mb-2">
            <AlertTriangle :size="20" class="text-red-600" />
            <h3 class="text-lg font-bold text-gray-900">Confirm Deletion</h3>
          </div>
          <p class="text-sm text-gray-600 mb-4">
            Are you sure you want to delete this fund? All transaction data will
            be permanently removed. The view-only wallet on monero-wallet-rpc
            will remain.
          </p>
          <div class="flex gap-3 justify-end">
            <Button variant="outline" @click="showDeleteModal = false"
              >Cancel</Button
            >
            <Button
              variant="destructive"
              :disabled="deleting"
              @click="deleteFund"
            >
              <div class="flex items-center space-x-1">
                <Loader2 v-if="deleting" :size="14" class="animate-spin" />
                <Trash2 v-else :size="14" />
                <span>{{ deleting ? "Deleting..." : "Delete" }}</span>
              </div>
            </Button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from "vue";
import { useRouter } from "vue-router";
import {
  LogOut,
  Save,
  CircleCheck,
  CircleX,
  Info,
  AlertTriangle,
  Trash2,
  Loader2,
  Eye,
  EyeOff,
  AlertCircle,
  PlusCircle,
} from "@lucide/vue";
import { useFundStore } from "@/stores/fund";
import { fundsApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { useDatetimeFormat } from "@/composables/useDatetimeFormat";

const router = useRouter();
const store = useFundStore();
const {
  formatDate: formatDatetime,
  loadFormat,
  updateFormat,
} = useDatetimeFormat();

const currentFund = computed(() => store.currentFund);
const maskedKey = computed(() => {
  const key = localStorage.getItem("xmr_api_key") || "";
  return key ? key.slice(0, 8) + "..." + key.slice(-4) : "Not set";
});

// Fund management state
const newLabel = ref(currentFund.value?.label || "");
const newDescription = ref(currentFund.value?.description || "");
const newTargetAmount = ref(currentFund.value?.target_amount_xmr || "");
const showDeleteModal = ref(false);
const savingLabel = ref(false);
const savingDescription = ref(false);
const savingTarget = ref(false);
const targetError = ref("");
const togglingActive = ref(false);
const deleting = ref(false);

// Create fund state
const createForm = reactive({
  label: "",
  description: "",
  primary_address: "",
  deposit_address: "",
  view_key: "",
  start_height: 3280000,
  target_amount_xmr: "",
});
const createError = ref("");
const creating = ref(false);
const showViewKey = ref(false);

// Datetime format state
const datetimeFormat = ref("YYYY-MM-DD HH:mm:ss");
const formatError = ref("");
const savingFormat = ref(false);

const formatExamples = [
  { pattern: "YYYY-MM-DD HH:mm:ss", output: "2026-06-17 14:30:00" },
  { pattern: "DD/MM/YYYY HH:mm", output: "17/06/2026 14:30" },
  { pattern: "MM-DD-YYYY", output: "06-17-2026" },
];

// Sync label when fund loads
watch(currentFund, (fund) => {
  if (fund) {
    newLabel.value = fund.label;
    newDescription.value = fund.description || "";
    newTargetAmount.value = fund.target_amount_xmr || "";
  }
});

// Load datetime format on mount
onMounted(async () => {
  try {
    const fmt = await loadFormat();
    datetimeFormat.value = fmt;
  } catch {
    // Use default format
  }
});

function handleLogout() {
  store.logout();
  router.push("/");
}

async function handleCreateFund() {
  createError.value = "";
  creating.value = true;
  try {
    const payload = { ...createForm };
    // Only send target_amount_xmr if it has a value
    if (!payload.target_amount_xmr?.trim()) {
      delete payload.target_amount_xmr;
    }
    // Only send deposit_address if it has a value, otherwise backend defaults to primary_address
    if (!payload.deposit_address?.trim()) {
      delete payload.deposit_address;
    }
    // Only send description if it has a value
    if (!payload.description?.trim()) {
      delete payload.description;
    }
    await store.createFund(payload);
    router.push("/");
  } catch (err: any) {
    createError.value = err.response?.data?.detail || "Failed to create fund";
  } finally {
    creating.value = false;
  }
}

async function updateLabel() {
  if (!currentFund.value) return;
  savingLabel.value = true;
  try {
    await fundsApi.update(currentFund.value.id, { label: newLabel.value });
    await store.fetchFund(currentFund.value.id);
  } catch {
    // Error handled silently
  } finally {
    savingLabel.value = false;
  }
}

async function updateDescription() {
  if (!currentFund.value) return;
  savingDescription.value = true;
  try {
    const value = newDescription.value.trim();
    await fundsApi.update(currentFund.value.id, {
      description: value || null,
    });
    await store.fetchFund(currentFund.value.id);
  } catch {
    // Error handled silently
  } finally {
    savingDescription.value = false;
  }
}

async function updateTargetAmount() {
  if (!currentFund.value) return;
  targetError.value = "";
  savingTarget.value = true;
  try {
    const value = newTargetAmount.value.trim();
    const payload: { target_amount_xmr?: string | null } = {};
    if (value === "") {
      // Clear the target
      payload.target_amount_xmr = null;
    } else {
      // Validate XMR precision (max 12 decimal places)
      const parsed = parseFloat(value);
      if (isNaN(parsed) || parsed <= 0) {
        targetError.value = "Enter a positive number";
        savingTarget.value = false;
        return;
      }
      const parts = value.split(".");
      if (parts.length > 1 && parts[1].length > 12) {
        targetError.value = "Maximum 12 decimal places allowed for XMR";
        savingTarget.value = false;
        return;
      }
      payload.target_amount_xmr = value;
    }
    await fundsApi.update(currentFund.value.id, payload);
    await store.fetchFund(currentFund.value.id);
  } catch (err: any) {
    targetError.value =
      err.response?.data?.detail || "Failed to update target amount";
  } finally {
    savingTarget.value = false;
  }
}

async function updateDatetimeFormat() {
  formatError.value = "";
  savingFormat.value = true;
  try {
    const pattern = await updateFormat(datetimeFormat.value.trim());
    datetimeFormat.value = pattern;
  } catch (err: any) {
    formatError.value = err.response?.data?.detail || "Failed to update format";
  } finally {
    savingFormat.value = false;
  }
}

async function toggleActive() {
  if (!currentFund.value) return;
  togglingActive.value = true;
  try {
    await fundsApi.update(currentFund.value.id, {
      is_active: !currentFund.value.is_active,
    });
    await store.fetchFund(currentFund.value.id);
  } catch {
    // Error handled silently
  } finally {
    togglingActive.value = false;
  }
}

async function deleteFund() {
  if (!currentFund.value) return;
  deleting.value = true;
  try {
    await fundsApi.delete(currentFund.value.id);
    store.currentFund = null;
    showDeleteModal.value = false;
    router.push("/");
  } catch {
    // Error handled silently
  } finally {
    deleting.value = false;
  }
}

function formatDate(dateStr: string): string {
  return formatDatetime(dateStr);
}
</script>
