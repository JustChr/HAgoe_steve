/* go-e + SteVe Smart Charging card — bundled, do not edit by hand. Source in /card. */
var Mt=Object.defineProperty;var Pt=Object.getOwnPropertyDescriptor;var y=(r,t,e,s)=>{for(var i=s>1?void 0:s?Pt(t,e):t,o=r.length-1,n;o>=0;o--)(n=r[o])&&(i=(s?n(t,e,i):n(i))||i);return s&&i&&Mt(t,e,i),i};var B=globalThis,F=B.ShadowRoot&&(B.ShadyCSS===void 0||B.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,tt=Symbol(),_t=new WeakMap,T=class{constructor(t,e,s){if(this._$cssResult$=!0,s!==tt)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o,e=this.t;if(F&&t===void 0){let s=e!==void 0&&e.length===1;s&&(t=_t.get(e)),t===void 0&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),s&&_t.set(e,t))}return t}toString(){return this.cssText}},mt=r=>new T(typeof r=="string"?r:r+"",void 0,tt),M=(r,...t)=>{let e=r.length===1?r[0]:t.reduce((s,i,o)=>s+(n=>{if(n._$cssResult$===!0)return n.cssText;if(typeof n=="number")return n;throw Error("Value passed to 'css' function must be a 'css' function result: "+n+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+r[o+1],r[0]);return new T(e,r,tt)},ft=(r,t)=>{if(F)r.adoptedStyleSheets=t.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let e of t){let s=document.createElement("style"),i=B.litNonce;i!==void 0&&s.setAttribute("nonce",i),s.textContent=e.cssText,r.appendChild(s)}},et=F?r=>r:r=>r instanceof CSSStyleSheet?(t=>{let e="";for(let s of t.cssRules)e+=s.cssText;return mt(e)})(r):r;var{is:zt,defineProperty:Lt,getOwnPropertyDescriptor:Ut,getOwnPropertyNames:jt,getOwnPropertySymbols:Dt,getPrototypeOf:It}=Object,V=globalThis,vt=V.trustedTypes,qt=vt?vt.emptyScript:"",Bt=V.reactiveElementPolyfillSupport,P=(r,t)=>r,z={toAttribute(r,t){switch(t){case Boolean:r=r?qt:null;break;case Object:case Array:r=r==null?r:JSON.stringify(r)}return r},fromAttribute(r,t){let e=r;switch(t){case Boolean:e=r!==null;break;case Number:e=r===null?null:Number(r);break;case Object:case Array:try{e=JSON.parse(r)}catch{e=null}}return e}},W=(r,t)=>!zt(r,t),yt={attribute:!0,type:String,converter:z,reflect:!1,useDefault:!1,hasChanged:W};Symbol.metadata??=Symbol("metadata"),V.litPropertyMetadata??=new WeakMap;var v=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=yt){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){let s=Symbol(),i=this.getPropertyDescriptor(t,s,e);i!==void 0&&Lt(this.prototype,t,i)}}static getPropertyDescriptor(t,e,s){let{get:i,set:o}=Ut(this.prototype,t)??{get(){return this[e]},set(n){this[e]=n}};return{get:i,set(n){let a=i?.call(this);o?.call(this,n),this.requestUpdate(t,a,s)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??yt}static _$Ei(){if(this.hasOwnProperty(P("elementProperties")))return;let t=It(this);t.finalize(),t.l!==void 0&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(P("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(P("properties"))){let e=this.properties,s=[...jt(e),...Dt(e)];for(let i of s)this.createProperty(i,e[i])}let t=this[Symbol.metadata];if(t!==null){let e=litPropertyMetadata.get(t);if(e!==void 0)for(let[s,i]of e)this.elementProperties.set(s,i)}this._$Eh=new Map;for(let[e,s]of this.elementProperties){let i=this._$Eu(e,s);i!==void 0&&this._$Eh.set(i,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){let e=[];if(Array.isArray(t)){let s=new Set(t.flat(1/0).reverse());for(let i of s)e.unshift(et(i))}else t!==void 0&&e.push(et(t));return e}static _$Eu(t,e){let s=e.attribute;return s===!1?void 0:typeof s=="string"?s:typeof t=="string"?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),this.renderRoot!==void 0&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){let t=new Map,e=this.constructor.elementProperties;for(let s of e.keys())this.hasOwnProperty(s)&&(t.set(s,this[s]),delete this[s]);t.size>0&&(this._$Ep=t)}createRenderRoot(){let t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return ft(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,s){this._$AK(t,s)}_$ET(t,e){let s=this.constructor.elementProperties.get(t),i=this.constructor._$Eu(t,s);if(i!==void 0&&s.reflect===!0){let o=(s.converter?.toAttribute!==void 0?s.converter:z).toAttribute(e,s.type);this._$Em=t,o==null?this.removeAttribute(i):this.setAttribute(i,o),this._$Em=null}}_$AK(t,e){let s=this.constructor,i=s._$Eh.get(t);if(i!==void 0&&this._$Em!==i){let o=s.getPropertyOptions(i),n=typeof o.converter=="function"?{fromAttribute:o.converter}:o.converter?.fromAttribute!==void 0?o.converter:z;this._$Em=i;let a=n.fromAttribute(e,o.type);this[i]=a??this._$Ej?.get(i)??a,this._$Em=null}}requestUpdate(t,e,s,i=!1,o){if(t!==void 0){let n=this.constructor;if(i===!1&&(o=this[t]),s??=n.getPropertyOptions(t),!((s.hasChanged??W)(o,e)||s.useDefault&&s.reflect&&o===this._$Ej?.get(t)&&!this.hasAttribute(n._$Eu(t,s))))return;this.C(t,e,s)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(t,e,{useDefault:s,reflect:i,wrapped:o},n){s&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,n??e??this[t]),o!==!0||n!==void 0)||(this._$AL.has(t)||(this.hasUpdated||s||(e=void 0),this._$AL.set(t,e)),i===!0&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let t=this.scheduleUpdate();return t!=null&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[i,o]of this._$Ep)this[i]=o;this._$Ep=void 0}let s=this.constructor.elementProperties;if(s.size>0)for(let[i,o]of s){let{wrapped:n}=o,a=this[i];n!==!0||this._$AL.has(i)||a===void 0||this.C(i,void 0,o,a)}}let t=!1,e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(s=>s.hostUpdate?.()),this.update(e)):this._$EM()}catch(s){throw t=!1,this._$EM(),s}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(t){}firstUpdated(t){}};v.elementStyles=[],v.shadowRootOptions={mode:"open"},v[P("elementProperties")]=new Map,v[P("finalized")]=new Map,Bt?.({ReactiveElement:v}),(V.reactiveElementVersions??=[]).push("2.1.2");var ct=globalThis,$t=r=>r,K=ct.trustedTypes,bt=K?K.createPolicy("lit-html",{createHTML:r=>r}):void 0,Ct="$lit$",$=`lit$${Math.random().toFixed(9).slice(2)}$`,Rt="?"+$,Ft=`<${Rt}>`,A=document,U=()=>A.createComment(""),j=r=>r===null||typeof r!="object"&&typeof r!="function",lt=Array.isArray,Vt=r=>lt(r)||typeof r?.[Symbol.iterator]=="function",st=`[ 	
\f\r]`,L=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,wt=/-->/g,xt=/>/g,w=RegExp(`>|${st}(?:([^\\s"'>=/]+)(${st}*=${st}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),At=/'/g,St=/"/g,kt=/^(?:script|style|textarea|title)$/i,dt=r=>(t,...e)=>({_$litType$:r,strings:t,values:e}),d=dt(1),ht=dt(2),ne=dt(3),S=Symbol.for("lit-noChange"),l=Symbol.for("lit-nothing"),Et=new WeakMap,x=A.createTreeWalker(A,129);function Nt(r,t){if(!lt(r)||!r.hasOwnProperty("raw"))throw Error("invalid template strings array");return bt!==void 0?bt.createHTML(t):t}var Wt=(r,t)=>{let e=r.length-1,s=[],i,o=t===2?"<svg>":t===3?"<math>":"",n=L;for(let a=0;a<e;a++){let c=r[a],p,u,h=-1,g=0;for(;g<c.length&&(n.lastIndex=g,u=n.exec(c),u!==null);)g=n.lastIndex,n===L?u[1]==="!--"?n=wt:u[1]!==void 0?n=xt:u[2]!==void 0?(kt.test(u[2])&&(i=RegExp("</"+u[2],"g")),n=w):u[3]!==void 0&&(n=w):n===w?u[0]===">"?(n=i??L,h=-1):u[1]===void 0?h=-2:(h=n.lastIndex-u[2].length,p=u[1],n=u[3]===void 0?w:u[3]==='"'?St:At):n===St||n===At?n=w:n===wt||n===xt?n=L:(n=w,i=void 0);let _=n===w&&r[a+1].startsWith("/>")?" ":"";o+=n===L?c+Ft:h>=0?(s.push(p),c.slice(0,h)+Ct+c.slice(h)+$+_):c+$+(h===-2?a:_)}return[Nt(r,o+(r[e]||"<?>")+(t===2?"</svg>":t===3?"</math>":"")),s]},D=class r{constructor({strings:t,_$litType$:e},s){let i;this.parts=[];let o=0,n=0,a=t.length-1,c=this.parts,[p,u]=Wt(t,e);if(this.el=r.createElement(p,s),x.currentNode=this.el.content,e===2||e===3){let h=this.el.content.firstChild;h.replaceWith(...h.childNodes)}for(;(i=x.nextNode())!==null&&c.length<a;){if(i.nodeType===1){if(i.hasAttributes())for(let h of i.getAttributeNames())if(h.endsWith(Ct)){let g=u[n++],_=i.getAttribute(h).split($),f=/([.?@])?(.*)/.exec(g);c.push({type:1,index:o,name:f[2],strings:_,ctor:f[1]==="."?rt:f[1]==="?"?ot:f[1]==="@"?nt:N}),i.removeAttribute(h)}else h.startsWith($)&&(c.push({type:6,index:o}),i.removeAttribute(h));if(kt.test(i.tagName)){let h=i.textContent.split($),g=h.length-1;if(g>0){i.textContent=K?K.emptyScript:"";for(let _=0;_<g;_++)i.append(h[_],U()),x.nextNode(),c.push({type:2,index:++o});i.append(h[g],U())}}}else if(i.nodeType===8)if(i.data===Rt)c.push({type:2,index:o});else{let h=-1;for(;(h=i.data.indexOf($,h+1))!==-1;)c.push({type:7,index:o}),h+=$.length-1}o++}}static createElement(t,e){let s=A.createElement("template");return s.innerHTML=t,s}};function k(r,t,e=r,s){if(t===S)return t;let i=s!==void 0?e._$Co?.[s]:e._$Cl,o=j(t)?void 0:t._$litDirective$;return i?.constructor!==o&&(i?._$AO?.(!1),o===void 0?i=void 0:(i=new o(r),i._$AT(r,e,s)),s!==void 0?(e._$Co??=[])[s]=i:e._$Cl=i),i!==void 0&&(t=k(r,i._$AS(r,t.values),i,s)),t}var it=class{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){let{el:{content:e},parts:s}=this._$AD,i=(t?.creationScope??A).importNode(e,!0);x.currentNode=i;let o=x.nextNode(),n=0,a=0,c=s[0];for(;c!==void 0;){if(n===c.index){let p;c.type===2?p=new I(o,o.nextSibling,this,t):c.type===1?p=new c.ctor(o,c.name,c.strings,this,t):c.type===6&&(p=new at(o,this,t)),this._$AV.push(p),c=s[++a]}n!==c?.index&&(o=x.nextNode(),n++)}return x.currentNode=A,i}p(t){let e=0;for(let s of this._$AV)s!==void 0&&(s.strings!==void 0?(s._$AI(t,s,e),e+=s.strings.length-2):s._$AI(t[e])),e++}},I=class r{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,s,i){this.type=2,this._$AH=l,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=s,this.options=i,this._$Cv=i?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode,e=this._$AM;return e!==void 0&&t?.nodeType===11&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=k(this,t,e),j(t)?t===l||t==null||t===""?(this._$AH!==l&&this._$AR(),this._$AH=l):t!==this._$AH&&t!==S&&this._(t):t._$litType$!==void 0?this.$(t):t.nodeType!==void 0?this.T(t):Vt(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==l&&j(this._$AH)?this._$AA.nextSibling.data=t:this.T(A.createTextNode(t)),this._$AH=t}$(t){let{values:e,_$litType$:s}=t,i=typeof s=="number"?this._$AC(t):(s.el===void 0&&(s.el=D.createElement(Nt(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===i)this._$AH.p(e);else{let o=new it(i,this),n=o.u(this.options);o.p(e),this.T(n),this._$AH=o}}_$AC(t){let e=Et.get(t.strings);return e===void 0&&Et.set(t.strings,e=new D(t)),e}k(t){lt(this._$AH)||(this._$AH=[],this._$AR());let e=this._$AH,s,i=0;for(let o of t)i===e.length?e.push(s=new r(this.O(U()),this.O(U()),this,this.options)):s=e[i],s._$AI(o),i++;i<e.length&&(this._$AR(s&&s._$AB.nextSibling,i),e.length=i)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){let s=$t(t).nextSibling;$t(t).remove(),t=s}}setConnected(t){this._$AM===void 0&&(this._$Cv=t,this._$AP?.(t))}},N=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,s,i,o){this.type=1,this._$AH=l,this._$AN=void 0,this.element=t,this.name=e,this._$AM=i,this.options=o,s.length>2||s[0]!==""||s[1]!==""?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=l}_$AI(t,e=this,s,i){let o=this.strings,n=!1;if(o===void 0)t=k(this,t,e,0),n=!j(t)||t!==this._$AH&&t!==S,n&&(this._$AH=t);else{let a=t,c,p;for(t=o[0],c=0;c<o.length-1;c++)p=k(this,a[s+c],e,c),p===S&&(p=this._$AH[c]),n||=!j(p)||p!==this._$AH[c],p===l?t=l:t!==l&&(t+=(p??"")+o[c+1]),this._$AH[c]=p}n&&!i&&this.j(t)}j(t){t===l?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}},rt=class extends N{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===l?void 0:t}},ot=class extends N{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==l)}},nt=class extends N{constructor(t,e,s,i,o){super(t,e,s,i,o),this.type=5}_$AI(t,e=this){if((t=k(this,t,e,0)??l)===S)return;let s=this._$AH,i=t===l&&s!==l||t.capture!==s.capture||t.once!==s.once||t.passive!==s.passive,o=t!==l&&(s===l||i);i&&this.element.removeEventListener(this.name,this,s),o&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}},at=class{constructor(t,e,s){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=s}get _$AU(){return this._$AM._$AU}_$AI(t){k(this,t)}};var Kt=ct.litHtmlPolyfillSupport;Kt?.(D,I),(ct.litHtmlVersions??=[]).push("3.3.3");var Ht=(r,t,e)=>{let s=e?.renderBefore??t,i=s._$litPart$;if(i===void 0){let o=e?.renderBefore??null;s._$litPart$=i=new I(t.insertBefore(U(),o),o,void 0,e??{})}return i._$AI(r),i};var pt=globalThis,m=class extends v{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){let e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=Ht(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return S}};m._$litElement$=!0,m.finalized=!0,pt.litElementHydrateSupport?.({LitElement:m});var Jt=pt.litElementPolyfillSupport;Jt?.({LitElement:m});(pt.litElementVersions??=[]).push("4.2.2");var J=r=>(t,e)=>{e!==void 0?e.addInitializer(()=>{customElements.define(r,t)}):customElements.define(r,t)};var Zt={attribute:!0,type:String,converter:z,reflect:!1,hasChanged:W},Gt=(r=Zt,t,e)=>{let{kind:s,metadata:i}=e,o=globalThis.litPropertyMetadata.get(i);if(o===void 0&&globalThis.litPropertyMetadata.set(i,o=new Map),s==="setter"&&((r=Object.create(r)).wrapped=!0),o.set(e.name,r),s==="accessor"){let{name:n}=e;return{set(a){let c=t.get.call(this);t.set.call(this,a),this.requestUpdate(n,c,r,!0,a)},init(a){return a!==void 0&&this.C(n,void 0,r,a),a}}}if(s==="setter"){let{name:n}=e;return function(a){let c=this[n];t.call(this,a),this.requestUpdate(n,c,r,!0,a)}}throw Error("Unsupported decorator location: "+s)};function H(r){return(t,e)=>typeof e=="object"?Gt(r,t,e):((s,i,o)=>{let n=i.hasOwnProperty(o);return i.constructor.createProperty(o,s),n?Object.getOwnPropertyDescriptor(i,o):void 0})(r,t,e)}function Z(r){return H({...r,state:!0,attribute:!1})}var E="goe_steve";function ut(r){let t=new Map;for(let e of Object.values(r.entities))if(!(e.platform!==E||!e.device_id)&&!t.has(e.device_id)){let s=r.devices[e.device_id];t.set(e.device_id,s?.name_by_user||s?.name||e.device_id)}return[...t.entries()].map(([e,s])=>({id:e,name:s}))}function Ot(r,t){let e={tag_energy:[]};if(!t){let o=ut(r);o.length===1&&(t=o[0].id)}if(e.deviceId=t,!t)return e;let s=Object.values(r.entities).filter(o=>o.platform===E&&o.device_id===t),i=o=>{let n=s.find(c=>c.translation_key===o);return n?n.entity_id:s.find(c=>{let p=c.entity_id.split(".")[1]??"";return p===o||p.endsWith(`_${o}`)})?.entity_id};return e.status=i("status"),e.power_flow=i("power_flow"),e.surplus=i("surplus_for_car"),e.target_current=i("target_current"),e.controlling=i("controlling"),e.charging_mode=i("charging_mode"),e.battery_policy=i("battery_policy"),e.smart_control=i("smart_control"),e.auto_phase=i("auto_phase"),e.battery_reserve_soc=i("battery_reserve_soc"),e.battery_floor_soc=i("battery_floor_soc"),e.target_energy=i("target_energy"),e.active_transaction=i("active_transaction"),e.last_session_energy=i("last_session_energy"),e.selected_tag=i("selected_tag"),e.tag_energy=s.filter(o=>o.translation_key==="tag_energy"||o.entity_id.split(".")[1]?.includes("_tag_energy_")).map(o=>o.entity_id).sort(),e}var gt={"card.no_device":"No {name} device found. Set one up first, then add this card.","card.default_title":"Smart Charging","flow.solar":"Solar","flow.grid":"Grid","flow.export":"Export","flow.battery":"Battery","flow.home":"Home","flow.car":"Car","flow.no_car":"No car","control.mode":"Mode","control.battery":"Battery","control.smart_control":"Smart control","control.auto_phase":"Auto phase (1\u21943)","control.reserve_soc":"Home battery reserve","control.floor_soc":"Home battery floor","control.target_energy":"Car target energy","control.tag":"Tag","action.authorize":"Authorize","action.start":"Start","action.stop":"Stop","session.none":"No active session","session.charging":"Charging: {state}","session.last":"Last session: {energy}","session.blocked":"blocked","session.tag":"tag","editor.device":"Smart Charging device (optional \u2014 auto-detected)","editor.title":"Title (optional)","editor.show_flow":"Show energy flow","editor.show_controls":"Show controls","editor.show_sessions":"Show sessions & RFID"},Yt={"card.no_device":"Kein {name}-Ger\xE4t gefunden. Richte zuerst eines ein und f\xFCge dann diese Karte hinzu.","card.default_title":"Intelligentes Laden","flow.solar":"Solar","flow.grid":"Netz","flow.export":"Einspeisung","flow.battery":"Batterie","flow.home":"Haus","flow.car":"Auto","flow.no_car":"Kein Auto","control.mode":"Modus","control.battery":"Batterie","control.smart_control":"Intelligente Steuerung","control.auto_phase":"Auto-Phase (1\u21943)","control.reserve_soc":"Hausspeicher-Reserve","control.floor_soc":"Hausspeicher-Minimum","control.target_energy":"Ziel-Energie Auto","control.tag":"Tag","action.authorize":"Freigeben","action.start":"Starten","action.stop":"Stoppen","session.none":"Kein aktiver Ladevorgang","session.charging":"L\xE4dt: {state}","session.last":"Letzter Ladevorgang: {energy}","session.blocked":"gesperrt","session.tag":"Tag","editor.device":"Smart-Charging-Ger\xE4t (optional \u2014 automatisch erkannt)","editor.title":"Titel (optional)","editor.show_flow":"Energiefluss anzeigen","editor.show_controls":"Steuerung anzeigen","editor.show_sessions":"Ladevorg\xE4nge & RFID anzeigen"},Qt={en:gt,de:Yt};function Xt(r){let t=(r?.locale?.language||r?.language||"en").toLowerCase().split("-")[0];return Qt[t]??gt}function b(r,t,e={}){let i=Xt(r)[t]??gt[t]??t;for(let[o,n]of Object.entries(e))i=i.replace(`{${o}}`,n);return i}var C=class extends m{constructor(){super(...arguments);this._schema=[{name:"device",selector:{device:{integration:E}}},{name:"title",selector:{text:{}}},{type:"grid",name:"",schema:[{name:"show_flow",selector:{boolean:{}}},{name:"show_controls",selector:{boolean:{}}},{name:"show_sessions",selector:{boolean:{}}}]}];this._label=e=>{switch(e.name){case"device":return b(this.hass,"editor.device");case"title":return b(this.hass,"editor.title");case"show_flow":return b(this.hass,"editor.show_flow");case"show_controls":return b(this.hass,"editor.show_controls");case"show_sessions":return b(this.hass,"editor.show_sessions");default:return e.name}}}setConfig(e){this._config=e}render(){return!this.hass||!this._config?l:d`<ha-form
      .hass=${this.hass}
      .data=${this._config}
      .schema=${this._schema}
      .computeLabel=${this._label}
      @value-changed=${this._valueChanged}
    ></ha-form>`}_valueChanged(e){let s={...e.detail.value};this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:s},bubbles:!0,composed:!0}))}};C.styles=M`
    ha-form {
      display: block;
      padding: 8px 0;
    }
  `,y([H({attribute:!1})],C.prototype,"hass",2),y([Z()],C.prototype,"_config",2),C=y([J("goe-steve-card-editor")],C);var te="go-e + SteVe Smart Charging",q=r=>{if(r==null||Number.isNaN(r))return"\u2014";let t=Math.abs(r);return t>=1e3?`${(r/1e3).toFixed(t>=1e4?0:1)} kW`:`${Math.round(r)} W`},R=class extends m{static getConfigElement(){return document.createElement("goe-steve-card-editor")}static getStubConfig(t){return{type:"custom:goe-steve-card",device:ut(t)[0]?.id}}setConfig(t){this._config={show_flow:!0,show_controls:!0,show_sessions:!0,...t}}getCardSize(){return 8}get _entities(){return this.hass?Ot(this.hass,this._config?.device):null}_t(t,e={}){return b(this.hass,t,e)}render(){if(!this.hass||!this._config)return l;let t=this._entities;if(!t||!t.deviceId)return d`<ha-card>
        <div class="empty">
          <ha-icon icon="mdi:ev-station"></ha-icon>
          <p>${this._renderNoDevice()}</p>
        </div>
      </ha-card>`;let e=this._config.title??this._deviceName(t.deviceId)??this._t("card.default_title");return d`<ha-card>
      ${this._renderHeader(t,e)}
      <div class="content">
        ${this._config.show_flow?this._renderFlow(t):l}
        ${this._config.show_controls?this._renderControls(t):l}
        ${this._config.show_sessions?this._renderSessions(t):l}
      </div>
    </ha-card>`}_renderNoDevice(){let[t,e]=this._t("card.no_device").split("{name}");return d`${t}<b>${te}</b>${e??""}`}_renderHeader(t,e){let s=this._stateObj(t.status),i=s?.state&&s.state!=="unknown"?s.state:"\u2014",o=this._isOn(t.controlling),n=this._displayState(t.charging_mode),a=this._displayState(t.battery_policy);return d`<div class="header">
      <div class="title-row">
        <ha-icon class="brain ${o?"active":""}" icon="mdi:brain"></ha-icon>
        <span class="title">${e}</span>
      </div>
      <div class="reason">${i}</div>
      <div class="chips">
        ${n?d`<span class="chip"><ha-icon icon="mdi:ev-station"></ha-icon>${n}</span>`:l}
        ${a?d`<span class="chip"><ha-icon icon="mdi:home-battery"></ha-icon>${a}</span>`:l}
      </div>
    </div>`}_renderFlow(t){let e=this._stateObj(t.power_flow),s=e?.attributes??{},i=Number(s.pv_w??NaN),o=Number(s.grid_w??NaN),n=s.battery_w===null||s.battery_w===void 0?null:Number(s.battery_w),a=Number(s.car_w??(e?e.state:NaN)),c=Number(s.house_w??NaN),p=s.battery_soc,u=s.car_connected,h=50,g=(f,O,Y,Q,X,Tt="")=>ht`
      <g class="node" transform="translate(${f},${O})">
        <circle r="26"></circle>
        <foreignObject x="-13" y="-20" width="26" height="26">
          <ha-icon icon="${Y}"></ha-icon>
        </foreignObject>
        <text class="node-val" y="14">${X}</text>
        <text class="node-lbl" y="42">${Q}${Tt}</text>
      </g>`,_=(f,O,Y,Q)=>{let X=O?Math.max(.6,3-Math.min(Q,9e3)/3e3):0;return ht`
        <path class="edge" d="${f}"></path>
        <path
          class="edge-flow ${O?"active":""} ${Y?"rev":""}"
          d="${f}"
          style="${O?`animation-duration:${X}s`:""}"
        ></path>`};return d`<div class="flow">
      <svg viewBox="0 0 320 320" preserveAspectRatio="xMidYMid meet">
        ${_("M160,66 L160,134",i>h,!1,i)}
        ${_("M76,160 L134,160",Number.isNaN(o)?!1:Math.abs(o)>h,o<0,Math.abs(o))}
        ${n!==null?_("M244,160 L186,160",Math.abs(n)>h,n>0,Math.abs(n)):l}
        ${_("M160,186 L160,244",a>h,!1,a)}

        ${g(160,40,"mdi:solar-power",this._t("flow.solar"),q(i))}
        ${g(40,160,"mdi:transmission-tower",o<0?this._t("flow.export"):this._t("flow.grid"),q(Math.abs(o)))}
        ${n!==null?g(280,160,"mdi:home-battery",this._t("flow.battery"),q(Math.abs(n)),p!=null?` ${Math.round(Number(p))}%`:""):l}
        ${g(160,160,"mdi:home",this._t("flow.home"),q(c))}
        ${g(160,280,u===!1?"mdi:car-off":"mdi:car-electric",u===!1?this._t("flow.no_car"):this._t("flow.car"),q(a))}
      </svg>
    </div>`}_renderControls(t){let e=this._stateObj(t.charging_mode),s=this._stateObj(t.battery_policy),i=this._stateObj(t.smart_control),o=this._stateObj(t.battery_reserve_soc),n=this._stateObj(t.battery_floor_soc),a=this._stateObj(t.target_energy),c=s?.state,p=e?.state;return d`<div class="controls">
      ${e?d`<div class="control">
            <span class="ctl-label">${this._t("control.mode")}</span>
            ${this._renderSelect(e)}
          </div>`:l}
      ${s?d`<div class="control">
            <span class="ctl-label">${this._t("control.battery")}</span>
            ${this._renderSelect(s)}
          </div>`:l}
      ${o&&c==="protect"?d`<div class="control">
            <span class="ctl-label">${this._t("control.reserve_soc")}</span>
            ${this._renderNumber(o)}
          </div>`:l}
      ${n&&c==="assist"?d`<div class="control">
            <span class="ctl-label">${this._t("control.floor_soc")}</span>
            ${this._renderNumber(n)}
          </div>`:l}
      ${a&&(p==="price"||p==="combined")?d`<div class="control">
            <span class="ctl-label">${this._t("control.target_energy")}</span>
            ${this._renderNumber(a)}
          </div>`:l}
      ${i?d`<div class="control">
            <span class="ctl-label">${this._t("control.smart_control")}</span>
            <ha-switch
              .checked=${this._isOn(t.smart_control)}
              @change=${u=>this._toggle(t.smart_control,u)}
            ></ha-switch>
          </div>`:l}
      ${t.auto_phase?d`<div class="control">
            <span class="ctl-label">${this._t("control.auto_phase")}</span>
            <ha-switch
              .checked=${this._isOn(t.auto_phase)}
              @change=${u=>this._toggle(t.auto_phase,u)}
            ></ha-switch>
          </div>`:l}
    </div>`}_renderNumber(t){let e=t.attributes,s=e.unit_of_measurement??"";return d`<span class="ctl-number-wrap">
      <input
        class="ctl-number"
        type="number"
        .value=${t.state}
        min=${e.min??l}
        max=${e.max??l}
        step=${e.step??l}
        @change=${i=>this._setNumber(t,i.target.value)}
      />
      ${s?d`<span class="ctl-unit">${s}</span>`:l}
    </span>`}_setNumber(t,e){let s=Number(e);Number.isNaN(s)||String(s)===t.state||this.hass.callService("number","set_value",{entity_id:t.entity_id,value:s})}_renderSelect(t){let e=t.attributes.options??[];return d`<select
      class="ctl-select"
      @change=${s=>this._selectOption(t,s.target.value)}
    >
      ${e.map(s=>d`<option .value=${s} ?selected=${s===t.state}>
            ${this._localizeOption(t,s)}
          </option>`)}
    </select>`}_renderSessions(t){let e=this._stateObj(t.active_transaction),s=this._stateObj(t.last_session_energy),i=this._stateObj(t.selected_tag),o=t.tag_energy.map(a=>this._stateObj(a)).filter(a=>!!a);if(!e&&!s&&!i&&o.length===0)return l;let n=!!e&&!["idle","unknown","unavailable",""].includes(e.state);return d`<div class="sessions">
      ${this._renderTagPicker(i,n)}
      ${e?d`<div class="session-row">
            <ha-icon icon="mdi:card-account-details"></ha-icon>
            <span>${e.state==="idle"?this._t("session.none"):this._t("session.charging",{state:e.attributes.name??e.state})}</span>
          </div>`:l}
      ${s&&s.state&&s.state!=="unknown"?d`<div class="session-row">
            <ha-icon icon="mdi:history"></ha-icon>
            <span>${this._t("session.last",{energy:this._fmtState(s)})}</span>
          </div>`:l}
      ${o.length?d`<div class="tags">
            ${o.map(a=>d`<div class="tag">
                <span class="tag-id">${a.attributes.name??a.attributes.id_tag??this._t("session.tag")}</span>
                <span class="tag-kwh ${a.attributes.blocked?"blocked":""}">
                  ${this._fmtState(a)}${a.attributes.blocked?` \xB7 ${this._t("session.blocked")}`:""}
                </span>
              </div>`)}
          </div>`:l}
    </div>`}_renderTagPicker(t,e){if(!t)return l;let s=t.attributes.options??[];if(s.length===0)return l;let i=s.includes(t.state);return d`<div class="tag-picker">
      ${e?l:d`<div class="control">
            <span class="ctl-label">${this._t("control.tag")}</span>
            ${this._renderSelect(t)}
          </div>`}
      <div class="tag-actions">
        ${e?d`<button
              class="tag-btn stop"
              @click=${()=>this._callTagService("remote_stop")}
            >
              <ha-icon icon="mdi:stop"></ha-icon>${this._t("action.stop")}
            </button>`:d`<button
                class="tag-btn"
                ?disabled=${!i}
                @click=${()=>this._callTagService("authorize_tag")}
              >
                <ha-icon icon="mdi:check-decagram"></ha-icon>${this._t("action.authorize")}
              </button>
              <button
                class="tag-btn"
                ?disabled=${!i}
                @click=${()=>this._callTagService("remote_start")}
              >
                <ha-icon icon="mdi:play"></ha-icon>${this._t("action.start")}
              </button>`}
      </div>
    </div>`}_callTagService(t){this.hass.callService(E,t,{})}_stateObj(t){return t?this.hass.states[t]:void 0}_isOn(t){return this._stateObj(t)?.state==="on"}_displayState(t){let e=this._stateObj(t);return e?this._fmtState(e):null}_fmtState(t){return this.hass.formatEntityState?this.hass.formatEntityState(t):t.state}_localizeOption(t,e){let s=this.hass.entities?.[t.entity_id]?.translation_key;if(s){let i=`component.${E}.entity.select.${s}.state.${e}`,o=this.hass.localize?.(i);if(o)return o}if(this.hass.formatEntityState){let i=this.hass.formatEntityState({...t,state:e},e);if(i)return i}return e}_deviceName(t){let e=this.hass.devices[t];return e?.name_by_user||e?.name||null}_selectOption(t,e){e!==t.state&&this.hass.callService("select","select_option",{entity_id:t.entity_id,option:e})}_toggle(t,e){if(!t)return;let s=e.target.checked;this.hass.callService("switch",s?"turn_on":"turn_off",{entity_id:t})}};R.styles=M`
    ha-card {
      overflow: hidden;
    }
    .empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      padding: 24px;
      color: var(--secondary-text-color);
      text-align: center;
    }
    .empty ha-icon {
      --mdc-icon-size: 40px;
      color: var(--disabled-text-color);
    }
    .header {
      padding: 16px 16px 8px;
    }
    .title-row {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .title {
      font-size: 1.25rem;
      font-weight: 500;
    }
    .brain {
      color: var(--disabled-text-color);
      transition: color 0.3s ease;
    }
    .brain.active {
      color: var(--primary-color);
    }
    .reason {
      margin-top: 4px;
      color: var(--secondary-text-color);
      font-size: 0.95rem;
      min-height: 1.2em;
    }
    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 10px;
    }
    .chip {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 3px 10px;
      border-radius: 14px;
      background: var(--secondary-background-color);
      font-size: 0.8rem;
      color: var(--primary-text-color);
    }
    .chip ha-icon {
      --mdc-icon-size: 15px;
      color: var(--primary-color);
    }
    .content {
      padding: 0 8px 8px;
    }

    /* Flow diagram */
    .flow svg {
      width: 100%;
      height: auto;
      max-height: 320px;
    }
    .node circle {
      fill: var(--card-background-color);
      stroke: var(--divider-color);
      stroke-width: 1.5;
    }
    .node ha-icon {
      --mdc-icon-size: 22px;
      color: var(--primary-color);
    }
    .node-val {
      text-anchor: middle;
      font-size: 11px;
      font-weight: 600;
      fill: var(--primary-text-color);
    }
    .node-lbl {
      text-anchor: middle;
      font-size: 10px;
      fill: var(--secondary-text-color);
    }
    .edge {
      fill: none;
      stroke: var(--divider-color);
      stroke-width: 2;
    }
    .edge-flow {
      fill: none;
      stroke: var(--primary-color);
      stroke-width: 3;
      stroke-linecap: round;
      stroke-dasharray: 4 10;
      opacity: 0;
    }
    .edge-flow.active {
      opacity: 0.9;
      animation-name: dash;
      animation-timing-function: linear;
      animation-iteration-count: infinite;
    }
    .edge-flow.active.rev {
      animation-name: dash-rev;
    }
    @keyframes dash {
      to {
        stroke-dashoffset: -14;
      }
    }
    @keyframes dash-rev {
      to {
        stroke-dashoffset: 14;
      }
    }

    /* Controls */
    .controls {
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding: 4px 8px 8px;
    }
    .control {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .ctl-label {
      color: var(--secondary-text-color);
      font-size: 0.9rem;
      white-space: nowrap;
    }
    .ctl-select {
      min-width: 180px;
      flex: 1;
      max-width: 60%;
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid var(--divider-color);
      background: var(--card-background-color, var(--ha-card-background));
      color: var(--primary-text-color);
      font-family: inherit;
      font-size: 0.95rem;
      cursor: pointer;
    }
    .ctl-select:focus {
      outline: none;
      border-color: var(--primary-color);
    }
    .ctl-number-wrap {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      flex: 1;
      max-width: 60%;
      justify-content: flex-end;
    }
    .ctl-number {
      width: 90px;
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid var(--divider-color);
      background: var(--card-background-color, var(--ha-card-background));
      color: var(--primary-text-color);
      font-family: inherit;
      font-size: 0.95rem;
      text-align: right;
    }
    .ctl-number:focus {
      outline: none;
      border-color: var(--primary-color);
    }
    .ctl-unit {
      color: var(--secondary-text-color);
      font-size: 0.85rem;
      white-space: nowrap;
    }

    /* Sessions */
    .sessions {
      border-top: 1px solid var(--divider-color);
      margin: 4px 8px 0;
      padding-top: 8px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .session-row {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.9rem;
      color: var(--primary-text-color);
    }
    .session-row ha-icon {
      --mdc-icon-size: 18px;
      color: var(--secondary-text-color);
    }
    .tags {
      display: flex;
      flex-direction: column;
      gap: 4px;
      margin-top: 2px;
    }
    .tag {
      display: flex;
      justify-content: space-between;
      font-size: 0.85rem;
      padding: 2px 0;
    }
    .tag-picker {
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding-bottom: 4px;
    }
    .tag-actions {
      display: flex;
      gap: 8px;
    }
    .tag-btn {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      flex: 1;
      justify-content: center;
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid var(--divider-color);
      background: var(--card-background-color, var(--ha-card-background));
      color: var(--primary-text-color);
      font-family: inherit;
      font-size: 0.9rem;
      cursor: pointer;
    }
    .tag-btn ha-icon {
      --mdc-icon-size: 18px;
      color: var(--primary-color);
    }
    .tag-btn:hover:not([disabled]) {
      border-color: var(--primary-color);
    }
    .tag-btn[disabled] {
      opacity: 0.5;
      cursor: default;
    }
    .tag-btn.stop {
      color: var(--error-color, #db4437);
    }
    .tag-btn.stop ha-icon {
      color: var(--error-color, #db4437);
    }
    .tag-btn.stop:hover:not([disabled]) {
      border-color: var(--error-color, #db4437);
    }
    .tag-id {
      color: var(--secondary-text-color);
    }
    .tag-kwh {
      font-weight: 600;
    }
    .tag-kwh.blocked {
      color: var(--error-color, #db4437);
      font-weight: 500;
    }
  `,y([H({attribute:!1})],R.prototype,"hass",2),y([Z()],R.prototype,"_config",2),R=y([J("goe-steve-card")],R);window.customCards=window.customCards||[];window.customCards.push({type:"goe-steve-card",name:"go-e + SteVe Smart Charging",description:"Live energy flow, charging mode & battery policy with the brain's reasoning, inline controls and per-RFID energy.",preview:!0,documentationURL:"https://github.com/JustChr/HAgoe_steve"});export{R as GoeSteveCard};
/*! Bundled license information:

@lit/reactive-element/css-tag.js:
  (**
   * @license
   * Copyright 2019 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/reactive-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/lit-html.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-element/lit-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/is-server.js:
  (**
   * @license
   * Copyright 2022 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/custom-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/property.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/state.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/event-options.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/base.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query-all.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query-async.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query-assigned-elements.js:
  (**
   * @license
   * Copyright 2021 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query-assigned-nodes.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)
*/
