<template>
  <div class="space-y-6">
    <!-- Loading -->
    <div v-if="loading" class="text-center py-16">
      <Loader2 class="mx-auto animate-spin text-monero-orange" :size="40" />
      <p class="text-gray-600 mt-4">{{ t("giveawaydetail.loading") }}</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="text-center py-16">
      <AlertTriangle class="mx-auto text-amber-500" :size="40" />
      <h2 class="text-xl font-bold text-gray-900 mt-4 mb-2">
        {{ t("giveawaydetail.errorTitle") }}
      </h2>
      <p class="text-gray-600 mb-4">{{ error }}</p>
      <Button variant="default" @click="retryLoad">{{ t("common.retry") }}</Button>
    </div>

    <!-- Not found -->
    <div v-else-if="!giveaway" class="text-center py-16">
      <Wallet class="mx-auto text-gray-400" :size="48" />
      <h2 class="text-2xl font-bold text-gray-900 mt-4 mb-2">
        {{ t("giveawaydetail.notFoundTitle") }}
      </h2>
      <p class="text-gray-600 mb-6">{{ t("giveawaydetail.notFoundDesc") }}</p>
      <router-link to="/wallets">
        <Button variant="default">
          <div class="flex items-center space-x-2">
            <ArrowLeft :size="18" />
            <span>{{ t("giveawaydetail.backToWallets") }}</span>
          </div>
        </Button>
      </router-link>
    </div>

    <template v-else>
      <!-- Breadcrumb -->
      <nav class="flex items-center space-x-2 text-sm text-gray-500 mb-4">
        <router-link to="/wallets" class="hover:text-monero-orange transition-colors">
          {{ t("nav.wallets") }}
        </router-link>
        <ChevronRight :size="14" />
        <router-link :to="`/wallets/${walletUuid}`" class="hover:text-monero-orange transition-colors">
          {{ t("walletdetail.walletSettings") }}
        </router-link>
        <ChevronRight :size="14" />
        <span class="text-gray-900 font-medium">{{ t("giveawaydetail.giveawaySettings") }}</span>
      </nav>

      <!-- Closed banner -->
      <div
        v-if="giveaway.is_closed"
        class="flex items-center space-x-2 text-sm text-blue-800 bg-blue-50 border border-blue-200 rounded-lg p-3"
      >
        <CheckCircle2 :size="16" class="flex-shrink-0" />
        <span>{{ t("giveawaydetail.cannotEditClosed") }}</span>
      </div

      <!-- Started banner: core fields are locked once the giveaway has begun -->
      <div
        v-if="!isScheduled && !isClosed"
        class="flex items-center space-x-2 text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-lg p-3"
      >
        <Lock :size="16" class="flex-shrink-0" />
        <span>{{ t("giveawaydetail.coreLocked") }}</span>
      </div

      <!-- Section 1: Giveaway settings -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center space-x-2">
            <Gift :size="20" class="text-monero-orange flex-shrink-0" />
            <h2 class="text-lg font-semibold text-gray-900">
              {{ t("giveawaydetail.giveawaySettings") }}
            </h2>
          </div>
          <button
            :disabled="togglingActive"
            class="inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-full transition-colors cursor-pointer disabled:opacity-50"
            :class="
              giveaway.is_active
                ? 'bg-green-100 text-green-800 hover:bg-green-200'
                : 'bg-red-100 text-red-800 hover:bg-red-200'
            "
            @click="showToggleModal = true"
          >
            <Loader2 v-if="togglingActive" :size="12" class="mr-1 animate-spin" />
            <template v-else>
              <Check v-if="giveaway.is_active" :size="12" class="mr-1" />
              <X v-else :size="12" class="mr-1" />
              {{ giveaway.is_active ? t("common.active") : t("common.inactive") }}
            </template>
          </button>
        </div>

        <form class="space-y-5" @submit.prevent="saveGiveaway">
          <!-- Title -->
          <div>
            <label for="g-title" class="block text-sm font-medium text-gray-700 mb-1">
              {{ t("giveaway.titleField") }} <span class="text-red-500">*</span>
            </label>
            <input
              id="g-title"
              v-model="form.title"
              type="text"
              required
              :disabled="giveaway.is_closed"
              :placeholder="t('giveaway.titlePh')"
              class="w-full h-9 px-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange text-sm disabled:bg-gray-100"
            />
          </div>

          <!-- Description -->
          <div>
            <label for="g-desc" class="block text-sm font-medium text-gray-700 mb-1">
              {{ t("giveaway.description") }}
              <span class="text-gray-400 text-xs ml-1">({{ t("common.optional") }})</span>
            </label>
            <textarea
              id="g-desc"
              v-model="form.description"
              rows="2"
              :disabled="giveaway.is_closed"
              :placeholder="t('giveaway.descriptionPh')"
              class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange resize-none disabled:bg-gray-100"
            />
          </div>

          <!-- Deposit address -->
          <div>
            <label for="g-addr" class="block text-sm font-medium text-gray-700 mb-1">
              {{ t("giveaway.depositAddress") }} <span class="text-red-500">*</span>
            </label>
            <div class="flex items-center space-x-2">
              <input
                id="g-addr"
                v-model="form.deposit_address"
                type="text"
                required
                :disabled="!isScheduled"
                class="flex-1 h-9 px-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange text-sm font-mono disabled:bg-gray-100"
              />
              <button
                type="button"
                class="text-gray-400 hover:text-monero-orange transition-colors flex-shrink-0"
                :title="t('common.copyAddress')"
                @click="copyDepositAddress"
              >
                <Copy :size="16" />
              </button>
            </div>
            <p v-if="depositAddressError" class="mt-1 text-xs text-red-600">
              {{ depositAddressError }}
            </p>
          </div>

          <!-- Min amount -->
          <div>
            <label for="g-min" class="block text-sm font-medium text-gray-700 mb-1">
              {{ t("giveaway.minAmount") }} <span class="text-red-500">*</span>
            </label>
            <input
              id="g-min"
              v-model="form.min_amount_xmr"
              type="number"
              step="any"
              min="0"
              required
              :disabled="!isScheduled"
              :placeholder="t('giveaway.minAmountPh')"
              class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-monero-orange focus:border-monero-orange disabled:bg-gray-100"
            />
          </div>

          <!-- Dates -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label for="g-start" class="block text-sm font-medium text-gray-700 mb-1">
                {{ t("giveaway.startDate") }} <span class="text-red-500">*</span>
              </label>
              <input
                id="g-start"
                v-model="form.start_date"
                type="datetime-local"
                required
                :disabled="!isScheduled"
                class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-monero-orange focus:border-monero-orange disabled:bg-gray-100"
              />
            </div>
            <div>
              <label for="g-end" class="block text-sm font-medium text-gray-700 mb-1">
                {{ t("giveaway.endDate") }} <span class="text-red-500">*</span>
              </label>
              <input
                id="g-end"
                v-model="form.end_date"
                type="datetime-local"
                required
                :disabled="!isScheduled"
                class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-monero-orange focus:border-monero-orange disabled:bg-gray-100"
              />
            </div>
          </div>

          <!-- Instructions after end -->
          <div>
            <label for="g-instr" class="block text-sm font-medium text-gray-700 mb-1">
              {{ t("giveaway.instructionsAfterEnd") }}
              <span class="text-gray-400 text-xs ml-1">({{ t("common.optional") }})</span>
            </label>
            <textarea
              id="g-instr"
              v-model="form.instructions_after_end"
              rows="3"
              :disabled="giveaway.is_closed"
              :placeholder="t('giveaway.instructionsPh')"
              class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange resize-none disabled:bg-gray-100"
            />
          </div>

          <!-- Public website -->
          <div>
            <label for="g-web" class="block text-sm font-medium text-gray-700 mb-1">
              {{ t("giveaway.publicWebsite") }}
              <span class="text-gray-400 text-xs ml-1">({{ t("common.optional") }})</span>
            </label>
            <input
              id="g-web"
              v-model="form.public_website"
              type="text"
              :disabled="giveaway.is_closed"
              :placeholder="t('fund.websitePh')"
              class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-monero-orange focus:border-monero-orange disabled:bg-gray-100"
            />
            <p class="text-xs text-gray-500 mt-1">{{ t("funddetail.websiteHint") }}</p>
          </div>

          <!-- Widget colors -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label for="g-bg" class="block text-sm font-medium text-gray-700 mb-1">
                {{ t("giveaway.widgetBgColor") }}
                <span class="text-gray-400">({{ t("common.optional") }})</span>
              </label>
              <div class="flex items-center space-x-2">
                <input
                  id="g-bg"
                  v-model="form.widget_background_color"
                  type="text"
                  placeholder="#1a1a2e"
                  :disabled="giveaway.is_closed"
                  class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-monero-orange focus:border-monero-orange disabled:bg-gray-100"
                />
                <div
                  v-if="form.widget_background_color"
                  class="w-9 h-9 rounded-lg border border-gray-300 flex-shrink-0"
                  :style="{ backgroundColor: form.widget_background_color }"
                />
              </div>
            </div>
            <div>
              <label for="g-tc" class="block text-sm font-medium text-gray-700 mb-1">
                {{ t("giveaway.widgetTextColor") }}
                <span class="text-gray-400">({{ t("common.optional") }})</span>
              </label>
              <div class="flex items-center space-x-2">
                <input
                  id="g-tc"
                  v-model="form.widget_text_color"
                  type="text"
                  placeholder="#ffffff"
                  :disabled="giveaway.is_closed"
                  class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-monero-orange focus:border-monero-orange disabled:bg-gray-100"
                />
                <div
                  v-if="form.widget_text_color"
                  class="w-9 h-9 rounded-lg border border-gray-300 flex-shrink-0"
                  :style="{ backgroundColor: form.widget_text_color }"
                />
              </div>
            </div>
          </div>

          <!-- Save error -->
          <div
            v-if="saveError"
            class="flex items-start space-x-2 text-sm text-red-800 bg-red-50 border border-red-200 rounded-lg p-3"
          >
            <AlertCircle :size="16" class="text-red-600 flex-shrink-0 mt-0.5" />
            <p>{{ saveError }}</p>
          </div>

          <!-- Save / Delete -->
          <div class="flex items-center justify-between pt-4 border-t border-gray-100">
            <Button
              variant="destructive"
              size="sm"
              @click="showDeleteModal = true"
            >
              <div class="flex items-center space-x-1.5">
                <Trash2 :size="14" />
                <span>{{ t("giveawaydetail.deleteGiveaway") }}</span>
              </div>
            </Button>
            <div class="flex items-center space-x-2">
              <p v-if="hasChanges" class="text-xs text-amber-600">
                {{ t("giveawaydetail.unsavedChanges") }}
              </p>
              <Button
                v-if="!giveaway.is_closed"
                type="submit"
                variant="default"
                :disabled="saving || !hasChanges"
              >
                <div class="flex items-center space-x-2">
                  <Loader2 v-if="saving" :size="16" class="animate-spin" />
                  <Save v-else :size="16" />
                  <span>{{ saving ? t("giveawaydetail.saving") : t("giveawaydetail.save") }}</span>
                </div>
              </Button>
            </div>
          </div>
        </form>
      </div>

      <!-- Section 2: Pick winner + winner announcement -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center space-x-2">
            <Trophy :size="20" class="text-monero-orange flex-shrink-0" />
            <h3 class="text-lg font-semibold text-gray-900">
              {{ t("giveawaydetail.winnerSection") }}
            </h3>
          </div>
          <Button
            v-if="!giveaway.is_closed"
            variant="default"
            :disabled="!canPickWinner || pickingWinner"
            @click="confirmPickWinner"
          >
            <div class="flex items-center space-x-2">
              <Loader2 v-if="pickingWinner" :size="16" class="animate-spin" />
              <Trophy v-else :size="16" />
              <span>
                {{ pickingWinner ? t("giveawaydetail.pickingWinner") : (canPickWinner ? t("giveawaydetail.pickWinner") : t("giveawaydetail.pickWinnerDisabled")) }}
              </span>
            </div>
          </Button>
        </div>

        <div
          v-if="pickError"
          class="flex items-start space-x-2 text-sm rounded-lg p-3 mb-4"
          :class="pickErrorKind === 'waiting' ? 'text-amber-800 bg-amber-50 border border-amber-200' : (pickErrorKind === 'date' ? 'text-gray-800 bg-gray-50 border border-gray-200' : 'text-red-800 bg-red-50 border border-red-200')"
        >
          <AlertCircle :size="16" class="flex-shrink-0 mt-0.5" />
          <p>{{ pickError }}</p>
        </div>

        <div v-if="giveaway.is_closed && giveaway.winner" class="space-y-4">
          <div class="flex items-center space-x-2 text-green-700">
            <CheckCircle2 :size="18" />
            <span class="font-semibold">{{ t("giveawaydetail.winnerAnnounced") }}</span>
          </div>

          <div
            v-if="giveaway.winner.winning_txid"
            class="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-2"
          >
            <div class="text-sm">
              <span class="text-gray-500">{{ t("giveawaydetail.winningTx") }}:</span>
              <span class="font-mono ml-2 break-all text-xs">
                {{ giveaway.winner.winning_txid }}
              </span>
            </div>
            <div class="text-sm">
              <span class="text-gray-500">{{ t("giveawaydetail.winningAmount") }}:</span>
              <span class="font-semibold ml-2 text-monero-orange">
                {{ giveaway.winner.winning_amount_xmr }} XMR
              </span>
            </div>
            <div v-if="giveaway.winner.winning_timestamp" class="text-sm">
              <span class="text-gray-500">{{ t("giveawaydetail.winningTime") }}:</span>
              <span class="ml-2">{{ formatDateTime(giveaway.winner.winning_timestamp) }}</span>
            </div>
          </div>
          <div v-else class="text-sm text-gray-600">
            {{ t("giveawaydetail.noEligibleEntries") }}
          </div>

          <!-- Seed block -->
          <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div class="text-sm font-semibold mb-2">{{ t("giveawaydetail.seedBlock") }}</div>
            <div class="text-sm">
              <span class="text-gray-500">{{ t("giveawaydetail.seedHeight") }}:</span>
              <span class="font-mono ml-2">{{ giveaway.winning_block_height ?? "—" }}</span>
            </div>
            <div class="text-sm break-all">
              <span class="text-gray-500">{{ t("giveawaydetail.seedHash") }}:</span>
              <span class="font-mono ml-2 text-xs">{{ giveaway.winning_block_hash ?? "—" }}</span>
            </div>
            <div class="text-xs text-gray-500 mt-2">
              {{ t("giveawaydetail.verifyNote") }}
            </div>
          </div>

          <div v-if="giveaway.instructions_after_end" class="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <div class="text-sm font-semibold mb-1">{{ t("giveawaydetail.instructionsTitle") }}</div>
            <p class="text-sm text-gray-700 whitespace-pre-wrap">{{ giveaway.instructions_after_end }}</p>
          </div>
        </div>
      </div>

      <!-- Section 3: Widget preview + embed -->
      <GiveawayWidgetPreview
        :public-uuid="giveaway.public_uuid"
        :giveaway-id="giveaway.id"
        :form-label="form.title"
        :form-description="form.description"
        :form-min-amount="form.min_amount_xmr"
        :form-start-date="isoStart"
        :form-end-date="isoEnd"
        :deposit-address="form.deposit_address"
        :base-color="form.widget_background_color || '#667eea'"
        :text-color="form.widget_text_color || '#ffffff'"
        :closed-preview="giveaway.is_closed"
        :entry-count="giveaway.stats?.eligible_count ?? 0"
        :total-received="giveaway.stats?.total_received_xmr || '0.00'"
        :winner-txid="giveaway.winner?.winning_txid ?? null"
        :winner-amount="giveaway.winner?.winning_amount_xmr ?? null"
        :winner-timestamp="giveaway.winner?.winning_timestamp ?? null"
        :winning-block-height="giveaway.winning_block_height"
        :winning-block-hash="giveaway.winning_block_hash"
        :instructions-after-end="giveaway.instructions_after_end"
      />

      <!-- Section 4: Static widget -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-1">
          {{ t("giveawaydetail.staticWidget") }}
        </h3>
        <p class="text-sm text-gray-600 mb-4">{{ t("giveawaydetail.staticWidgetDesc") }}</p>
        <div class="mb-6">
          <div v-if="staticWidgetLoading" class="text-center py-8">
            <Loader2 class="mx-auto animate-spin text-monero-orange" :size="24" />
            <p class="text-gray-500 mt-2 text-sm">{{ t("giveawaydetail.staticWidgetLoading") }}</p>
          </div>
          <div v-else class="flex flex-col md:flex-row gap-5 p-6 rounded-lg" :style="{ background: gradientStyle, color: form.widget_text_color || '#ffffff' }">
            <div class="flex-1 min-w-0">
              <div class="text-sm opacity-90 mb-2">🎁 {{ form.title }}</div>
              <div v-if="form.description" class="text-sm opacity-80 mb-2">{{ form.description }}</div>
              <div v-if="form.min_amount_xmr" class="text-sm opacity-90 mb-1">
                Min entry: <b>{{ form.min_amount_xmr }} XMR</b>
              </div>
              <div class="text-xs opacity-80">Starts: {{ formatStaticDate(isoStart) }}</div>
              <div class="text-xs opacity-80">Ends: {{ formatStaticDate(isoEnd) }}</div>
            </div>
            <div class="flex flex-col items-center shrink-0">
              <img
                v-if="staticWidgetQr"
                :src="staticWidgetQr"
                alt="QR Code"
                class="w-[140px] h-[140px] block rounded-lg bg-white p-1"
              />
              <div class="text-[10px] opacity-70 break-all mt-2 text-center w-[140px]">
                {{ displayStaticAddress }}
              </div>
              <button
                type="button"
                class="mt-1 text-xs px-2.5 py-1 rounded-md border cursor-pointer"
                :style="{ borderColor: form.widget_text_color || '#ffffff', color: form.widget_text_color || '#ffffff', background: 'transparent', opacity: 0.9 }"
                @click="copyStaticAddress"
              >
                {{ copiedStaticAddress ? t("common.copied") : t("funddetail.copyAddress") }}
              </button>
            </div>
          </div>
          <div class="text-[11px] opacity-60 pt-3 mt-2" :style="{ color: form.widget_text_color || '#ffffff' }">
            Giveaway widget powered by xmrfts.com
          </div>
        </div>
        <div class="mb-6">
          <p class="text-sm font-medium text-gray-700 mb-2">{{ t("giveawaydetail.staticEmbedCode") }}</p>
          <div class="relative">
            <pre class="bg-gray-900 text-gray-100 p-4 rounded-lg text-sm font-mono overflow-x-auto max-h-64"><code>{{ staticWidgetSnippet }}</code></pre>
            <button
              class="absolute top-2 right-2 px-2 py-1 bg-gray-700 text-gray-200 rounded hover:bg-gray-600 transition-colors flex items-center gap-1 text-xs"
              @click="copyStaticEmbedCode"
            >
              {{ copiedStaticEmbed ? t("common.copied") : t("common.copyEmbedCode") }}
            </button>
          </div>
        </div>
        <p class="text-xs text-gray-500 flex items-center space-x-1">
          <AlertCircle :size="12" />
          <span>{{ t("giveawaydetail.staticWidgetNote") }}</span>
        </p>
      </div>


      <!-- Confirm pick-winner modal -->
      <ConfirmDialog
        :open="showPickModal"
        :title="t('giveawaydetail.pickWinner')"
        :message="t('giveawaydetail.pickWinnerConfirm')"
        :confirm-text="t('giveawaydetail.pickWinner')"
        :cancel-text="t('common.cancel')"
        :loading="pickingWinner"
        :loading-text="t('giveawaydetail.pickingWinner')"
        confirm-variant="default"
        icon-bg-class="bg-orange-100"
        @confirm="pickWinner"
        @cancel="showPickModal = false"
      >
        <template #icon>
          <Trophy :size="20" class="text-monero-orange" />
        </template>
        <template #confirm-icon>
          <Trophy :size="14" />
        </template>
      </ConfirmDialog>

      <!-- Delete modal -->
      <ConfirmDialog
        :open="showDeleteModal"
        :title="t('giveawaydetail.deleteGiveaway')"
        :message="t('giveawaydetail.deleteMsg')"
        :confirm-text="t('common.delete')"
        :cancel-text="t('common.cancel')"
        :loading="deleting"
        :loading-text="t('giveawaydetail.deleting')"
        confirm-variant="destructive"
        icon-bg-class="bg-red-100"
        icon-text-class="text-red-600"
        @confirm="deleteGiveaway"
        @cancel="showDeleteModal = false"
      >
        <template #icon>
          <Trash2 :size="20" class="text-red-600" />
        </template>
      </ConfirmDialog>

      <!-- Toggle active modal -->
      <ConfirmDialog
        :open="showToggleModal"
        :title="giveaway.is_active ? t('giveawaydetail.deactivateGiveaway') : t('giveawaydetail.activateGiveaway')"
        :message="giveaway.is_active ? t('giveawaydetail.deactivateMsg') : t('giveawaydetail.activateMsg')"
        :confirm-text="giveaway.is_active ? t('common.deactivate') : t('common.activate')"
        :cancel-text="t('common.cancel')"
        :loading="togglingActive"
        :loading-text="t('common.processing')"
        :confirm-variant="giveaway.is_active ? 'destructive' : 'default'"
        @confirm="toggleActive"
        @cancel="showToggleModal = false"
      >
        <template #icon>
          <X v-if="giveaway.is_active" :size="20" class="text-red-600" />
          <Check v-else :size="20" class="text-green-600" />
        </template>
      </ConfirmDialog>

      <!-- Start-now confirmation: moving start_date to now/past -->
      <ConfirmDialog
        :open="showStartConfirmModal"
        :title="t('giveawaydetail.startNowConfirmTitle')"
        :message="t('giveawaydetail.startNowConfirmMsg')"
        :confirm-text="t('giveawaydetail.startNowConfirmBtn')"
        :cancel-text="t('common.cancel')"
        :loading="saving"
        :loading-text="t('common.saving')"
        confirm-variant="destructive"
        icon-bg-class="bg-amber-100"
        icon-text-class="text-amber-600"
        @confirm="confirmStartNowSave"
        @cancel="showStartConfirmModal = false"
      >
        <template #icon>
          <AlertCircle :size="20" class="text-amber-600" />
        </template>
      </ConfirmDialog>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  Gift,
  Trophy,
  Loader2,
  AlertTriangle,
  AlertCircle,
  Wallet,
  ArrowLeft,
  Check,
  CheckCircle2,
  X,
  Copy,
  Trash2,
  Save,
  ChevronRight,
  Lock,
} from "@lucide/vue";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/dialog";
import GiveawayWidgetPreview from "@/components/Widget/GiveawayWidgetPreview.vue";
import {
  giveawaysApi,
  walletsApi,
  type Giveaway,
} from "@/lib/api";
import { useDatetimeFormat } from "@/composables/useDatetimeFormat";
import { useI18n } from "@/composables/useI18n";

const route = useRoute();
const router = useRouter();
const { loadFormat, formatDate: formatWithPattern } = useDatetimeFormat();
const { t } = useI18n();

const walletUuid = computed(() => route.params.walletUuid as string);
const giveawayUuid = computed(() => route.params.giveawayUuid as string);

const giveaway = ref<Giveaway | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
const saving = ref(false);
const saveError = ref("");
const depositAddressError = ref<string | null>(null);

// Pick winner
const showPickModal = ref(false);
const pickingWinner = ref(false);
const pickError = ref("");
const pickErrorKind = ref<"date" | "waiting" | "daemon">("date");

// Delete
const showDeleteModal = ref(false);
const deleting = ref(false);

// Toggle active
const showToggleModal = ref(false);
const togglingActive = ref(false);

// Start-now confirmation (moving start_date to now/past on a scheduled giveaway)
const showStartConfirmModal = ref(false);
const pendingPayload = ref<Record<string, unknown> | null>(null);

// Copy
const copiedAddress = ref(false);
const copiedStaticEmbed = ref(false);
const copiedStaticAddress = ref(false);

// Static widget
const staticWidgetQr = ref("");
const staticWidgetLoading = ref(false);

const form = ref({
  title: "",
  description: "",
  deposit_address: "",
  min_amount_xmr: "",
  start_date: "",
  end_date: "",
  instructions_after_end: "",
  public_website: "",
  widget_background_color: "",
  widget_text_color: "",
});

function formatDateTime(s: string | null): string {
  if (!s) return "—";
  return formatWithPattern(s);
}

// Convert datetime-local string <-> ISO
function toLocalInput(iso: string): string {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "";
  const off = d.getTimezoneOffset();
  const local = new Date(d.getTime() - off * 60 * 1000);
  return local.toISOString().slice(0, 16);
}
function toIso(local: string): string {
  if (!local) return "";
  const d = new Date(local);
  if (isNaN(d.getTime())) return "";
  return d.toISOString();
}
const isoStart = computed(() => toIso(form.value.start_date));
const isoEnd = computed(() => toIso(form.value.end_date));

const canPickWinner = computed(() => {
  if (!giveaway.value || giveaway.value.is_closed) return false;
  return Date.now() >= new Date(giveaway.value.end_date).getTime();
});

// Lifecycle status mirrors the backend (scheduled | active | ended | closed).
const giveawayStatus = computed(() => giveaway.value?.status ?? "scheduled");
const isScheduled = computed(() => giveawayStatus.value === "scheduled");
const isClosed = computed(() => giveawayStatus.value === "closed");

// Build a PATCH payload containing only the fields that actually changed.
// Core fields (deposit_address, min_amount, start/end date) are only sent
// while the giveaway is still scheduled — once started they are locked by
// the backend, so we must not include them (sending an unchanged value would
// still trip the backend's model_fields_set core-lock check).
function buildUpdatePayload(): Record<string, unknown> {
  const g = giveaway.value;
  if (!g) return {};
  const payload: Record<string, unknown> = {};
  const sched = isScheduled.value;
  if (form.value.title !== g.title) {
    payload.title = form.value.title.trim() || g.title;
  }
  if (form.value.description !== (g.description || "")) {
    payload.description = form.value.description.trim() || null;
  }
  if (form.value.instructions_after_end !== (g.instructions_after_end || "")) {
    payload.instructions_after_end = form.value.instructions_after_end.trim() || null;
  }
  if (form.value.public_website !== (g.public_website || "")) {
    payload.public_website = form.value.public_website.trim() || null;
  }
  if (form.value.widget_background_color !== (g.widget_background_color || "")) {
    payload.widget_background_color = form.value.widget_background_color || null;
  }
  if (form.value.widget_text_color !== (g.widget_text_color || "")) {
    payload.widget_text_color = form.value.widget_text_color || null;
  }
  if (sched) {
    if (form.value.deposit_address !== g.deposit_address) {
      payload.deposit_address = form.value.deposit_address.trim();
    }
    if (form.value.min_amount_xmr !== (g.min_amount_xmr || "")) {
      payload.min_amount_xmr = form.value.min_amount_xmr;
    }
    if (new Date(isoStart.value).getTime() !== new Date(g.start_date).getTime()) {
      payload.start_date = isoStart.value;
    }
    if (new Date(isoEnd.value).getTime() !== new Date(g.end_date).getTime()) {
      payload.end_date = isoEnd.value;
    }
  }
  return payload;
}

const hasChanges = computed(() => Object.keys(buildUpdatePayload()).length > 0);

// True when the user is moving start_date from the future to now/past on a
// scheduled giveaway — an irreversible transition that locks core fields.
const startNowPending = computed(() => {
  const g = giveaway.value;
  if (!g || !isScheduled.value) return false;
  if (!("start_date" in buildUpdatePayload())) return false;
  return new Date(isoStart.value).getTime() <= Date.now();
});

// Gradient for static widget preview
function hexToHsl(hex: string): [number, number, number] {
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0,
    s = 0;
  const l = (max + min) / 2;
  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
    else if (max === g) h = ((b - r) / d + 2) / 6;
    else h = ((r - g) / d + 4) / 6;
  }
  return [Math.round(h * 360), Math.round(s * 100), Math.round(l * 100)];
}
function hslToHex(h: number, s: number, l: number): string {
  h = ((h % 360) + 360) % 360;
  const sn = s / 100;
  const ln = l / 100;
  const c = (1 - Math.abs(2 * ln - 1)) * sn;
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = ln - c / 2;
  let r = 0,
    g = 0,
    b = 0;
  if (h < 60) {
    r = c;
    g = x;
  } else if (h < 120) {
    r = x;
    g = c;
  } else if (h < 180) {
    g = c;
    b = x;
  } else if (h < 240) {
    g = x;
    b = c;
  } else if (h < 300) {
    r = x;
    b = c;
  } else {
    r = c;
    b = x;
  }
  const toHex = (v: number) =>
    Math.round((v + m) * 255)
      .toString(16)
      .padStart(2, "0");
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}
const gradientEndColor = computed(() => {
  const [h, s, l] = hexToHsl(form.value.widget_background_color || "#667eea");
  return hslToHex(h + 40, s, l);
});
const gradientStyle = computed(
  () =>
    `linear-gradient(135deg, ${form.value.widget_background_color || "#667eea"} 0%, ${gradientEndColor.value} 100%)`,
);

const staticWidgetSnippet = computed(() => {
  const bgColor = form.value.widget_background_color || "#667eea";
  const textColor = form.value.widget_text_color || "#ffffff";
  const endColor = gradientEndColor.value;
  const label = (form.value.title || t("giveaway.titleSingular")).replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const desc = (form.value.description || "").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const minAmt = form.value.min_amount_xmr || "";
  const addr = form.value.deposit_address || "";
  const addrShort = addr.length > 20 ? addr.slice(0, 10) + "..." + addr.slice(-10) : addr;
  const qr = staticWidgetQr.value || "";
  const startStr = formatStaticDate(isoStart.value);
  const endStr = formatStaticDate(isoEnd.value);
  const descHtml = desc
    ? `<div style="font-size:12px;opacity:0.8;margin-bottom:6px;">${desc}</div>`
    : "";
  const minHtml = minAmt
    ? `<div style="font-size:13px;opacity:0.9;margin-bottom:6px;">Min entry: ${minAmt} XMR</div>`
    : "";
  const qrImg = qr
    ? `<img src="${qr}" alt="QR Code" style="width:140px;height:140px;border-radius:8px;background:#fff;padding:4px;" />`
    : "";
  return `<!-- XMR Fund Transparency Suite — Static Giveaway Widget (zero requests) -->
<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:linear-gradient(135deg,${bgColor} 0%,${endColor} 100%);color:${textColor};padding:24px;border-radius:12px;box-shadow:0 4px 6px rgba(0,0,0,0.1);max-width:500px;width:100%;display:flex;flex-direction:column;">
<div style="display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap;">
<div style="flex:1;min-width:200px;">
<div style="font-size:14px;opacity:0.9;margin-bottom:8px;">&#127873; ${label}</div>
${descHtml}${minHtml}
<div style="font-size:11px;opacity:0.8;">Starts: ${startStr}</div>
<div style="font-size:11px;opacity:0.8;">Ends: ${endStr}</div>
</div>
<div style="display:flex;flex-direction:column;align-items:center;min-width:140px;">
${qrImg}
<div style="font-size:10px;opacity:0.7;word-break:break-all;margin-top:8px;text-align:center;">${addrShort}</div>
<button data-addr="${addr}" onclick="xmrStaticGiveawayCopyAddr(this)" style="margin-top:6px;font-size:11px;padding:4px 10px;border-radius:6px;border:1px solid ${textColor};background:transparent;color:${textColor};cursor:pointer;opacity:0.9;">Copy Address</button>
</div>
</div>
<div style="font-size:11px;opacity:0.6;padding-top:12px;"><a href="https://xmrfts.com" target="_blank" rel="noopener noreferrer" style="color:inherit;text-decoration:none;">Giveaway widget powered by xmrfts.com</a></div>
</div>
<script>
function xmrStaticGiveawayCopyAddr(btn){var a=btn.getAttribute('data-addr');function d(){btn.textContent='Copy Address';}function f(){var t=document.createElement('textarea');t.value=a;t.style.position='fixed';t.style.left='-9999px';t.style.opacity='0';document.body.appendChild(t);t.focus();t.select();document.execCommand('copy');document.body.removeChild(t);btn.textContent='Copied!';setTimeout(d,2000);}try{if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(a).then(function(){btn.textContent='Copied!';setTimeout(d,2000);}).catch(f);}else{f();}}catch(e){f();}}
${"\u003c/"}script>`;
});

async function loadGiveaway() {
  loading.value = true;
  error.value = null;
  try {
    const walletsResponse = await walletsApi.list();
    const wallet = walletsResponse.data.find((w) => w.uuid === walletUuid.value);
    if (!wallet) {
      giveaway.value = null;
      error.value = "Wallet not found";
      return;
    }
    const list = await giveawaysApi.list(wallet.id);
    const found = list.data.find((g) => g.public_uuid === giveawayUuid.value);
    if (!found) {
      giveaway.value = null;
      error.value = "Giveaway not found";
      return;
    }
    const detail = await giveawaysApi.get(found.id);
    giveaway.value = detail.data;
    syncForm();
    await loadStaticWidget();
  } catch (err: any) {
    if (err.response?.status === 401) {
      error.value = "Authentication required";
    } else {
      error.value = err.response?.data?.detail || "Failed to load giveaway";
    }
  } finally {
    loading.value = false;
  }
}

function syncForm() {
  if (!giveaway.value) return;
  form.value = {
    title: giveaway.value.title,
    description: giveaway.value.description || "",
    deposit_address: giveaway.value.deposit_address,
    min_amount_xmr: giveaway.value.min_amount_xmr || "",
    start_date: toLocalInput(giveaway.value.start_date),
    end_date: toLocalInput(giveaway.value.end_date),
    instructions_after_end: giveaway.value.instructions_after_end || "",
    public_website: giveaway.value.public_website || "",
    widget_background_color: giveaway.value.widget_background_color || "",
    widget_text_color: giveaway.value.widget_text_color || "",
  };
}

async function loadStaticWidget() {
  if (!giveaway.value) return;
  staticWidgetLoading.value = true;
  try {
    const res = await giveawaysApi.staticWidget(giveaway.value.id);
    staticWidgetQr.value = res.data.qr_data_url;
  } catch {
    staticWidgetQr.value = "";
  } finally {
    staticWidgetLoading.value = false;
  }
}

async function retryLoad() {
  await loadGiveaway();
}

// Persist the payload built by buildUpdatePayload(). Date consistency is
// enforced both here and in the backend.
async function doSave(payload: Record<string, unknown>) {
  saving.value = true;
  saveError.value = "";
  try {
    const res = await giveawaysApi.update(giveaway.value!.id, payload);
    giveaway.value = res.data;
    syncForm();
    await loadStaticWidget();
  } catch (err: any) {
    saveError.value = err.response?.data?.detail || "Failed to save changes";
  } finally {
    saving.value = false;
  }
}

async function saveGiveaway() {
  if (!giveaway.value) return;
  const payload = buildUpdatePayload();
  if (Object.keys(payload).length === 0) return;

  // Date consistency check (defensive — backend also enforces).
  if (isoStart.value && isoEnd.value) {
    if (new Date(isoStart.value).getTime() >= new Date(isoEnd.value).getTime()) {
      saveError.value = t("giveawaydetail.startAfterEnd");
      return;
    }
  }

  // Moving start_date to now/past on a scheduled giveaway starts it
  // immediately and irreversibly locks the core fields — confirm first.
  if (startNowPending.value) {
    pendingPayload.value = payload;
    showStartConfirmModal.value = true;
    return;
  }
  await doSave(payload);
}

async function confirmStartNowSave() {
  showStartConfirmModal.value = false;
  if (pendingPayload.value) {
    await doSave(pendingPayload.value);
    pendingPayload.value = null;
  }
}

async function toggleActive() {
  if (!giveaway.value) return;
  togglingActive.value = true;
  try {
    const res = await giveawaysApi.update(giveaway.value.id, {
      is_active: !giveaway.value.is_active,
    });
    giveaway.value = res.data;
    showToggleModal.value = false;
  } catch {
    // ignore
  } finally {
    togglingActive.value = false;
  }
}

function confirmPickWinner() {
  pickError.value = "";
  showPickModal.value = true;
}

async function pickWinner() {
  if (!giveaway.value) return;
  pickingWinner.value = true;
  pickError.value = "";
  try {
    const res = await giveawaysApi.pickWinner(giveaway.value.id);
    giveaway.value = res.data;
    showPickModal.value = false;
  } catch (err: any) {
    const status = err.response?.status;
    const detail = err.response?.data?.detail || "Failed to pick winner";
    pickErrorKind.value =
      status === 422 ? "waiting" : status === 409 ? "date" : "daemon";
    pickError.value =
      status === 422
        ? t("giveawaydetail.waitingForBlock")
        : status === 409
          ? t("giveawaydetail.endDateNotPassed")
          : t("giveawaydetail.daemonError");
    showPickModal.value = false;
    // surface detail in console for debugging
    console.warn("pick-winner failed:", detail);
  } finally {
    pickingWinner.value = false;
  }
}

async function deleteGiveaway() {
  if (!giveaway.value) return;
  deleting.value = true;
  try {
    await giveawaysApi.delete(giveaway.value.id);
    showDeleteModal.value = false;
    router.push(`/wallets/${walletUuid.value}`);
  } catch {
    // keep modal open
  } finally {
    deleting.value = false;
  }
}

async function copyToClipboard(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    // fallthrough
  }
  try {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.left = "-9999px";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    document.execCommand("copy");
    document.body.removeChild(ta);
    return true;
  } catch {
    return false;
  }
}

async function copyDepositAddress() {
  if (!giveaway.value) return;
  const ok = await copyToClipboard(form.value.deposit_address);
  if (ok) {
    copiedAddress.value = true;
    setTimeout(() => (copiedAddress.value = false), 2000);
  }
}

async function copyStaticEmbedCode() {
  const ok = await copyToClipboard(staticWidgetSnippet.value);
  if (ok) {
    copiedStaticEmbed.value = true;
    setTimeout(() => (copiedStaticEmbed.value = false), 2000);
  }
}

async function copyStaticAddress() {
  if (!giveaway.value) return;
  const ok = await copyToClipboard(form.value.deposit_address);
  if (ok) {
    copiedStaticAddress.value = true;
    setTimeout(() => (copiedStaticAddress.value = false), 2000);
  }
}

const displayStaticAddress = computed(() => {
  const a = form.value.deposit_address || "";
  if (a.length <= 20) return a;
  return a.slice(0, 10) + "..." + a.slice(-10);
});

function formatStaticDate(iso: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

onMounted(async () => {
  await loadFormat();
  await loadGiveaway();
});
</script>