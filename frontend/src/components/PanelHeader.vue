<script setup>
import { computed } from "vue";
import BrandMark from "./BrandMark.vue";
import SessionsMenu from "./SessionsMenu.vue";
import { Button, FeatherIcon } from "@/lib/ui";
import { useStore } from "@/store";
import { PANEL_PLACEMENTS } from "@/lib/panelLayout";
import { __ } from "@/lib/translate";

const props = defineProps({ onTogglePopOut: { type: Function, default: null } });
const emit = defineEmits(["close"]);
const { recentSessions, switchSession, newChat, panelPlacement, chatIconAllowed, chatIconWanted } =
	useStore();
const toggleChatIcon = () => (chatIconWanted.value = !chatIconWanted.value);
const isFloating = computed(() => panelPlacement.value === PANEL_PLACEMENTS.FLOATING);
const canPopOut = computed(() => panelPlacement.value !== PANEL_PLACEMENTS.COVERING);
</script>

<template>
	<header
		class="flex items-center gap-1.5 border-b border-outline-gray-1 px-3 py-2"
		:class="{ 'cursor-move touch-none select-none': isFloating }"
	>
		<BrandMark :size="18" />
		<span class="text-sm font-medium text-ink-gray-9">{{ __("Flow") }}</span>
		<span class="flex-1"></span>

		<SessionsMenu :sessions="recentSessions" @select="switchSession" />

		<Button
			v-if="chatIconAllowed"
			:variant="chatIconWanted ? 'subtle' : 'ghost'"
			:title="chatIconWanted ? __('Hide the chat icon') : __('Show the chat icon')"
			:aria-pressed="chatIconWanted"
			@click="toggleChatIcon"
		>
			<template #icon
				><FeatherIcon name="message-circle" :stroke-width="2" class="h-3.5 w-3.5"
			/></template>
		</Button>

		<Button variant="ghost" :title="__('New chat')" @click="newChat">
			<template #icon
				><FeatherIcon name="plus" :stroke-width="2" class="h-3.5 w-3.5"
			/></template>
		</Button>
		<Button
			v-if="canPopOut"
			variant="ghost"
			:title="isFloating ? __('Dock beside the page') : __('Pop out')"
			@click="props.onTogglePopOut && props.onTogglePopOut()"
		>
			<template #icon
				><FeatherIcon
					:name="isFloating ? 'sidebar' : 'external-link'"
					:stroke-width="2"
					class="h-3.5 w-3.5"
					:class="{ '-scale-x-100': isFloating }"
			/></template>
		</Button>
		<Button variant="ghost" :title="__('Close (Ctrl+I)')" @click="emit('close')">
			<template #icon
				><FeatherIcon name="x" :stroke-width="2" class="h-3.5 w-3.5"
			/></template>
		</Button>
	</header>
</template>
